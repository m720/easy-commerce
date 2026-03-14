from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import or_
from fastapi import HTTPException
from app.models.product import Product, ProductVariant, ProductImage, product_tags
from app.models.tag import Tag
from app.schemas.product import ProductCreate, ProductUpdate, ProductVariantCreate, ProductVariantUpdate
from app.services.s3_service import generate_read_url


def _enrich_images(product: Product):
    for img in product.images:
        img.url = generate_read_url(img.s3_key)
    return product


def list_products(
    db: Session,
    skip: int = 0,
    limit: int = 20,
    search: Optional[str] = None,
    category_id: Optional[int] = None,
    tag_id: Optional[int] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    is_featured: Optional[bool] = None,
    is_active: Optional[bool] = True,
) -> List[Product]:
    q = db.query(Product)
    if is_active is not None:
        q = q.filter(Product.is_active == is_active)
    if search:
        q = q.filter(Product.name.ilike(f"%{search}%"))
    if category_id:
        q = q.filter(Product.category_id == category_id)
    if tag_id:
        q = q.filter(Product.tags.any(Tag.id == tag_id))
    if min_price is not None:
        q = q.filter(Product.base_price >= min_price)
    if max_price is not None:
        q = q.filter(Product.base_price <= max_price)
    if is_featured is not None:
        q = q.filter(Product.is_featured == is_featured)
    products = q.offset(skip).limit(limit).all()
    return [_enrich_images(p) for p in products]


def get_product_or_404(product_id: UUID, db: Session) -> Product:
    product = db.query(Product).filter(Product.id == product_id, Product.is_active == True).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return _enrich_images(product)


def get_product_admin(product_id: UUID, db: Session) -> Product:
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return _enrich_images(product)


def create_product(data: ProductCreate, db: Session) -> Product:
    product = Product(
        name=data.name,
        description=data.description,
        base_price=data.base_price,
        category_id=data.category_id,
        is_featured=data.is_featured,
    )
    if data.tag_ids:
        tags = db.query(Tag).filter(Tag.id.in_(data.tag_ids)).all()
        product.tags = tags
    db.add(product)
    db.commit()
    db.refresh(product)
    return _enrich_images(product)


def update_product(product_id: UUID, data: ProductUpdate, db: Session) -> Product:
    product = get_product_admin(product_id, db)
    update_data = data.model_dump(exclude_unset=True)
    tag_ids = update_data.pop("tag_ids", None)
    for k, v in update_data.items():
        setattr(product, k, v)
    if tag_ids is not None:
        tags = db.query(Tag).filter(Tag.id.in_(tag_ids)).all()
        product.tags = tags
    db.commit()
    db.refresh(product)
    return _enrich_images(product)


def soft_delete_product(product_id: UUID, db: Session) -> None:
    product = get_product_admin(product_id, db)
    product.is_active = False
    db.commit()


def toggle_featured(product_id: UUID, db: Session) -> Product:
    product = get_product_admin(product_id, db)
    product.is_featured = not product.is_featured
    db.commit()
    db.refresh(product)
    return _enrich_images(product)


def bulk_set_active(product_ids: List[UUID], is_active: bool, db: Session) -> int:
    result = db.query(Product).filter(Product.id.in_(product_ids)).all()
    for p in result:
        p.is_active = is_active
    db.commit()
    return len(result)


# --- Variants ---

def list_variants(product_id: UUID, db: Session) -> List[ProductVariant]:
    get_product_or_404(product_id, db)
    return db.query(ProductVariant).filter(ProductVariant.product_id == product_id).all()


def create_variant(product_id: UUID, data: ProductVariantCreate, db: Session) -> ProductVariant:
    get_product_admin(product_id, db)
    if db.query(ProductVariant).filter(ProductVariant.sku == data.sku).first():
        raise HTTPException(status_code=400, detail="SKU already exists")
    variant = ProductVariant(product_id=product_id, **data.model_dump())
    db.add(variant)
    db.commit()
    db.refresh(variant)
    return variant


def update_variant(variant_id: UUID, data: ProductVariantUpdate, db: Session) -> ProductVariant:
    variant = db.query(ProductVariant).filter(ProductVariant.id == variant_id).first()
    if not variant:
        raise HTTPException(status_code=404, detail="Variant not found")
    update_data = data.model_dump(exclude_unset=True)
    if "sku" in update_data and update_data["sku"] != variant.sku:
        if db.query(ProductVariant).filter(ProductVariant.sku == update_data["sku"]).first():
            raise HTTPException(status_code=400, detail="SKU already exists")
    for k, v in update_data.items():
        setattr(variant, k, v)
    db.commit()
    db.refresh(variant)
    return variant


def delete_variant(variant_id: UUID, db: Session) -> None:
    variant = db.query(ProductVariant).filter(ProductVariant.id == variant_id).first()
    if not variant:
        raise HTTPException(status_code=404, detail="Variant not found")
    db.delete(variant)
    db.commit()
