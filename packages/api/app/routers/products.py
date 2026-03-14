from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from app.dependencies import get_db, require_admin, get_current_user, Pagination
from app.schemas.product import (
    ProductCreate, ProductUpdate, ProductResponse, ProductVariantCreate,
    ProductVariantUpdate, ProductVariantResponse, ProductImageResponse,
    BulkProductIds, UploadUrlRequest, UploadUrlResponse, ConfirmImageUpload,
)
from app.services import product_service
from app.services.s3_service import generate_upload_url, generate_read_url, delete_object
from app.models.product import ProductImage
import uuid as uuid_lib

router = APIRouter(prefix="/products", tags=["Products"])


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
    db: Session = Depends(get_db),
):
    return product_service.list_products(
        db=db, skip=pagination.skip, limit=pagination.limit,
        search=search, category_id=category_id, tag_id=tag_id,
        min_price=min_price, max_price=max_price, is_featured=is_featured,
    )


@router.get("/featured", response_model=List[ProductResponse])
def featured_products(pagination: Pagination = Depends(), db: Session = Depends(get_db)):
    return product_service.list_products(db=db, skip=pagination.skip, limit=pagination.limit, is_featured=True)


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: UUID, db: Session = Depends(get_db)):
    return product_service.get_product_or_404(product_id, db)


# --- Admin product endpoints ---

@router.post("", response_model=ProductResponse, status_code=201)
def create_product(data: ProductCreate, db: Session = Depends(get_db), _=Depends(require_admin)):
    return product_service.create_product(data, db)


@router.put("/{product_id}", response_model=ProductResponse)
def update_product(product_id: UUID, data: ProductUpdate, db: Session = Depends(get_db), _=Depends(require_admin)):
    return product_service.update_product(product_id, data, db)


@router.delete("/{product_id}", status_code=204)
def delete_product(product_id: UUID, db: Session = Depends(get_db), _=Depends(require_admin)):
    product_service.soft_delete_product(product_id, db)


@router.patch("/{product_id}/feature", response_model=ProductResponse)
def toggle_featured(product_id: UUID, db: Session = Depends(get_db), _=Depends(require_admin)):
    return product_service.toggle_featured(product_id, db)


@router.post("/bulk-activate", status_code=200)
def bulk_activate(data: BulkProductIds, db: Session = Depends(get_db), _=Depends(require_admin)):
    count = product_service.bulk_set_active(data.product_ids, True, db)
    return {"updated": count}


@router.post("/bulk-deactivate", status_code=200)
def bulk_deactivate(data: BulkProductIds, db: Session = Depends(get_db), _=Depends(require_admin)):
    count = product_service.bulk_set_active(data.product_ids, False, db)
    return {"updated": count}


# --- Variants ---

@router.get("/{product_id}/variants", response_model=List[ProductVariantResponse])
def list_variants(product_id: UUID, db: Session = Depends(get_db)):
    return product_service.list_variants(product_id, db)


@router.post("/{product_id}/variants", response_model=ProductVariantResponse, status_code=201)
def create_variant(product_id: UUID, data: ProductVariantCreate, db: Session = Depends(get_db), _=Depends(require_admin)):
    return product_service.create_variant(product_id, data, db)


@router.put("/{product_id}/variants/{variant_id}", response_model=ProductVariantResponse)
def update_variant(product_id: UUID, variant_id: UUID, data: ProductVariantUpdate, db: Session = Depends(get_db), _=Depends(require_admin)):
    return product_service.update_variant(variant_id, data, db)


@router.delete("/{product_id}/variants/{variant_id}", status_code=204)
def delete_variant(product_id: UUID, variant_id: UUID, db: Session = Depends(get_db), _=Depends(require_admin)):
    product_service.delete_variant(variant_id, db)


# --- Images ---

@router.get("/{product_id}/images", response_model=List[ProductImageResponse])
def list_images(product_id: UUID, db: Session = Depends(get_db)):
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
    return image


@router.delete("/{product_id}/images/{image_id}", status_code=204)
def delete_image(product_id: UUID, image_id: UUID, db: Session = Depends(get_db), _=Depends(require_admin)):
    image = db.query(ProductImage).filter(ProductImage.id == image_id, ProductImage.product_id == product_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    delete_object(image.s3_key)
    db.delete(image)
    db.commit()
