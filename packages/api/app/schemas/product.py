from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from decimal import Decimal
from datetime import datetime
from app.schemas.tag import TagResponse
from app.schemas.category import CategoryResponse


class ProductVariantBase(BaseModel):
    name: str
    sku: str
    price: Decimal
    stock_quantity: int = 0
    low_stock_threshold: int = 5


class ProductVariantCreate(ProductVariantBase):
    pass


class ProductVariantUpdate(BaseModel):
    name: Optional[str] = None
    sku: Optional[str] = None
    price: Optional[Decimal] = None
    stock_quantity: Optional[int] = None
    low_stock_threshold: Optional[int] = None


class ProductVariantResponse(ProductVariantBase):
    model_config = {"from_attributes": True}
    id: UUID
    product_id: UUID


class ProductImageResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: UUID
    product_id: UUID
    s3_key: str
    is_primary: bool
    sort_order: int
    url: Optional[str] = None  # populated by service from pre-signed URL


class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    base_price: Decimal
    category_id: Optional[int] = None
    is_featured: bool = False


class ProductCreate(ProductBase):
    tag_ids: List[int] = []


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    base_price: Optional[Decimal] = None
    category_id: Optional[int] = None
    is_featured: Optional[bool] = None
    is_active: Optional[bool] = None
    tag_ids: Optional[List[int]] = None


class ProductResponse(ProductBase):
    model_config = {"from_attributes": True}
    id: UUID
    is_active: bool
    created_at: datetime
    category: Optional[CategoryResponse] = None
    tags: List[TagResponse] = []
    variants: List[ProductVariantResponse] = []
    images: List[ProductImageResponse] = []


class BulkProductIds(BaseModel):
    product_ids: List[UUID]


class UploadUrlRequest(BaseModel):
    filename: str
    content_type: str = "image/jpeg"


class UploadUrlResponse(BaseModel):
    upload_url: str
    s3_key: str


class ConfirmImageUpload(BaseModel):
    s3_key: str
    is_primary: bool = False
    sort_order: int = 0
