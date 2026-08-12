from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from app.dependencies import get_db, get_read_db, require_admin, admin_audit, Pagination
from app.config import settings
from app.core import cache
from app.schemas.product import (
    ProductCreate, ProductUpdate, ProductResponse, ProductVariantCreate,
    ProductVariantUpdate, ProductVariantResponse, ProductImageResponse,
    BulkProductIds, UploadUrlRequest, UploadUrlResponse, ConfirmImageUpload,
)
from app.services import product_service
from app.services.audit_service import AuditAction, AuditContext, diff, snapshot
from app.services.s3_service import generate_upload_url, generate_read_url, delete_object
from app.models.product import ProductImage
import uuid as uuid_lib

router = APIRouter(prefix="/products", tags=["Products"])

# Fields worth reconstructing from an audit trail months later.
_PRODUCT_AUDITED_FIELDS = ("name", "description", "base_price", "category_id", "is_featured", "is_active")
_VARIANT_AUDITED_FIELDS = ("name", "sku", "price", "stock_quantity", "low_stock_threshold")


def _serialise(products) -> list[dict]:
    return [ProductResponse.model_validate(p).model_dump(mode="json") for p in products]


# --- Public product endpoints ---

@router.get("", response_model=List[ProductResponse])
def list_products(
    search: Optional[str] = Query(None),
    category_id: Optional[int] = Query(None),
    tag_id: Optional[int] = Query(None),
    min_price: Optional[float] = Query(None),
    max_price: Optional[float] = Query(None),
    is_featured: Optional[bool] = Query(None),
    pagination: Pagination = Depends(),
    db: Session = Depends(get_read_db),
):
    """Catalogue listing: cache-aside, replica-routed.

    The cache key covers every filter, so distinct queries do not collide; any
    admin write bumps the namespace version and orphans all of them at once.
    """
    key = cache.build_key(
        cache.CATALOG_NAMESPACE,
        "products",
        f"q={search}",
        f"cat={category_id}",
        f"tag={tag_id}",
        f"min={min_price}",
        f"max={max_price}",
        f"feat={is_featured}",
        f"skip={pagination.skip}",
        f"limit={pagination.limit}",
    )

    def loader():
        return _serialise(product_service.list_products(
            db=db, skip=pagination.skip, limit=pagination.limit,
            search=search, category_id=category_id, tag_id=tag_id,
            min_price=min_price, max_price=max_price, is_featured=is_featured,
        ))

    return cache.get_or_set(key, settings.CACHE_TTL_PRODUCT_LIST, loader)


@router.get("/featured", response_model=List[ProductResponse])
def featured_products(pagination: Pagination = Depends(), db: Session = Depends(get_read_db)):
    key = cache.build_key(
        cache.CATALOG_NAMESPACE,
        "products:featured",
        f"skip={pagination.skip}",
        f"limit={pagination.limit}",
    )

    def loader():
        return _serialise(product_service.list_products(
            db=db, skip=pagination.skip, limit=pagination.limit, is_featured=True
        ))

    return cache.get_or_set(key, settings.CACHE_TTL_PRODUCT_LIST, loader)


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: UUID, db: Session = Depends(get_read_db)):
    key = cache.build_key(cache.CATALOG_NAMESPACE, "product", product_id)

    def loader():
        product = product_service.get_product_or_404(product_id, db)
        return ProductResponse.model_validate(product).model_dump(mode="json")

    # TTL stays well under S3_PRESIGNED_URL_EXPIRY so cached image URLs cannot
    # outlive their signature.
    return cache.get_or_set(key, settings.CACHE_TTL_PRODUCT_DETAIL, loader)


# --- Admin product endpoints ---
# Every mutation below invalidates the catalogue namespace and leaves an audit
# entry. Both are cheap; a stale storefront or an unattributable price change
# is not.

@router.post("", response_model=ProductResponse, status_code=201)
def create_product(data: ProductCreate, db: Session = Depends(get_db), audit: AuditContext = Depends(admin_audit)):
    product = product_service.create_product(data, db)
    audit.record(
        db,
        action=AuditAction.PRODUCT_CREATED,
        entity_type="product",
        entity_id=product.id,
        entity_label=product.name,
        changes={f: {"before": None, "after": v} for f, v in snapshot(product, _PRODUCT_AUDITED_FIELDS).items()},
    )
    cache.invalidate()
    return product


@router.put("/{product_id}", response_model=ProductResponse)
def update_product(product_id: UUID, data: ProductUpdate, db: Session = Depends(get_db), audit: AuditContext = Depends(admin_audit)):
    before = snapshot(product_service.get_product_admin(product_id, db), _PRODUCT_AUDITED_FIELDS)
    product = product_service.update_product(product_id, data, db)
    audit.record(
        db,
        action=AuditAction.PRODUCT_UPDATED,
        entity_type="product",
        entity_id=product.id,
        entity_label=product.name,
        changes=diff(before, snapshot(product, _PRODUCT_AUDITED_FIELDS)),
    )
    cache.invalidate()
    return product


@router.delete("/{product_id}", status_code=204)
def delete_product(product_id: UUID, db: Session = Depends(get_db), audit: AuditContext = Depends(admin_audit)):
    product = product_service.get_product_admin(product_id, db)
    label = product.name
    product_service.soft_delete_product(product_id, db)
    audit.record(
        db,
        action=AuditAction.PRODUCT_DELETED,
        entity_type="product",
        entity_id=product_id,
        entity_label=label,
        changes={"is_active": {"before": True, "after": False}},
    )
    cache.invalidate()


@router.patch("/{product_id}/feature", response_model=ProductResponse)
def toggle_featured(product_id: UUID, db: Session = Depends(get_db), audit: AuditContext = Depends(admin_audit)):
    product = product_service.toggle_featured(product_id, db)
    audit.record(
        db,
        action=AuditAction.PRODUCT_FEATURED_TOGGLED,
        entity_type="product",
        entity_id=product.id,
        entity_label=product.name,
        changes={"is_featured": {"before": not product.is_featured, "after": product.is_featured}},
    )
    cache.invalidate()
    return product


@router.post("/bulk-activate", status_code=200)
def bulk_activate(data: BulkProductIds, db: Session = Depends(get_db), audit: AuditContext = Depends(admin_audit)):
    count = product_service.bulk_set_active(data.product_ids, True, db)
    audit.record(
        db,
        action=AuditAction.PRODUCT_BULK_ACTIVATION,
        entity_type="product",
        entity_label=f"{count} products",
        changes={
            "is_active": {"before": False, "after": True},
            "product_ids": {"before": None, "after": [str(pid) for pid in data.product_ids]},
        },
    )
    cache.invalidate()
    return {"updated": count}


@router.post("/bulk-deactivate", status_code=200)
def bulk_deactivate(data: BulkProductIds, db: Session = Depends(get_db), audit: AuditContext = Depends(admin_audit)):
    count = product_service.bulk_set_active(data.product_ids, False, db)
    audit.record(
        db,
        action=AuditAction.PRODUCT_BULK_ACTIVATION,
        entity_type="product",
        entity_label=f"{count} products",
        changes={
            "is_active": {"before": True, "after": False},
            "product_ids": {"before": None, "after": [str(pid) for pid in data.product_ids]},
        },
    )
    cache.invalidate()
    return {"updated": count}


# --- Variants ---

@router.get("/{product_id}/variants", response_model=List[ProductVariantResponse])
def list_variants(product_id: UUID, db: Session = Depends(get_read_db)):
    return product_service.list_variants(product_id, db)


@router.post("/{product_id}/variants", response_model=ProductVariantResponse, status_code=201)
def create_variant(product_id: UUID, data: ProductVariantCreate, db: Session = Depends(get_db), audit: AuditContext = Depends(admin_audit)):
    variant = product_service.create_variant(product_id, data, db)
    audit.record(
        db,
        action=AuditAction.VARIANT_CREATED,
        entity_type="product_variant",
        entity_id=variant.id,
        entity_label=variant.sku,
        changes={f: {"before": None, "after": v} for f, v in snapshot(variant, _VARIANT_AUDITED_FIELDS).items()},
    )
    cache.invalidate()
    return variant


@router.put("/{product_id}/variants/{variant_id}", response_model=ProductVariantResponse)
def update_variant(product_id: UUID, variant_id: UUID, data: ProductVariantUpdate, db: Session = Depends(get_db), audit: AuditContext = Depends(admin_audit)):
    existing = product_service.get_variant_or_404(variant_id, db)
    before = snapshot(existing, _VARIANT_AUDITED_FIELDS)
    variant = product_service.update_variant(variant_id, data, db)
    # Price and stock edits are the ones a finance or inventory question comes
    # back to, so they get the same treatment as any other field: recorded.
    audit.record(
        db,
        action=AuditAction.VARIANT_UPDATED,
        entity_type="product_variant",
        entity_id=variant.id,
        entity_label=variant.sku,
        changes=diff(before, snapshot(variant, _VARIANT_AUDITED_FIELDS)),
    )
    cache.invalidate()
    return variant


@router.delete("/{product_id}/variants/{variant_id}", status_code=204)
def delete_variant(product_id: UUID, variant_id: UUID, db: Session = Depends(get_db), audit: AuditContext = Depends(admin_audit)):
    existing = product_service.get_variant_or_404(variant_id, db)
    label = existing.sku
    product_service.delete_variant(variant_id, db)
    audit.record(
        db,
        action=AuditAction.VARIANT_DELETED,
        entity_type="product_variant",
        entity_id=variant_id,
        entity_label=label,
    )
    cache.invalidate()


# --- Images ---

@router.get("/{product_id}/images", response_model=List[ProductImageResponse])
def list_images(product_id: UUID, db: Session = Depends(get_read_db)):
    product = product_service.get_product_or_404(product_id, db)
    images = []
    for img in product.images:
        img.url = generate_read_url(img.s3_key)
        images.append(img)
    return images


@router.post("/{product_id}/images/upload-url", response_model=UploadUrlResponse)
def get_upload_url(product_id: UUID, data: UploadUrlRequest, db: Session = Depends(get_db), _=Depends(require_admin)):
    product_service.get_product_admin(product_id, db)
    s3_key = f"products/{product_id}/{uuid_lib.uuid4()}_{data.filename}"
    url = generate_upload_url(s3_key, data.content_type)
    return {"upload_url": url, "s3_key": s3_key}


@router.post("/{product_id}/images", response_model=ProductImageResponse, status_code=201)
def confirm_image(product_id: UUID, data: ConfirmImageUpload, db: Session = Depends(get_db), _=Depends(require_admin)):
    product_service.get_product_admin(product_id, db)
    if data.is_primary:
        db.query(ProductImage).filter(ProductImage.product_id == product_id).update({"is_primary": False})
    image = ProductImage(
        product_id=product_id,
        s3_key=data.s3_key,
        is_primary=data.is_primary,
        sort_order=data.sort_order,
    )
    db.add(image)
    db.commit()
    db.refresh(image)
    image.url = generate_read_url(image.s3_key)
    cache.invalidate()
    return image


@router.patch("/{product_id}/images/{image_id}/primary", response_model=ProductImageResponse)
def set_primary_image(product_id: UUID, image_id: UUID, db: Session = Depends(get_db), _=Depends(require_admin)):
    db.query(ProductImage).filter(ProductImage.product_id == product_id).update({"is_primary": False})
    image = db.query(ProductImage).filter(ProductImage.id == image_id, ProductImage.product_id == product_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    image.is_primary = True
    db.commit()
    db.refresh(image)
    image.url = generate_read_url(image.s3_key)
    cache.invalidate()
    return image


@router.delete("/{product_id}/images/{image_id}", status_code=204)
def delete_image(product_id: UUID, image_id: UUID, db: Session = Depends(get_db), _=Depends(require_admin)):
    image = db.query(ProductImage).filter(ProductImage.id == image_id, ProductImage.product_id == product_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    delete_object(image.s3_key)
    db.delete(image)
    db.commit()
    cache.invalidate()
