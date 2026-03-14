from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID
from decimal import Decimal
from app.schemas.product import ProductVariantResponse


class CartItemAdd(BaseModel):
    variant_id: UUID
    quantity: int = 1


class CartItemUpdate(BaseModel):
    quantity: int


class CartItemResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    variant_id: UUID
    quantity: int
    variant: ProductVariantResponse
    in_stock: bool = True


class CartResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    items: List[CartItemResponse]
    subtotal: Decimal
