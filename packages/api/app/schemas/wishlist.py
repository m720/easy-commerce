from pydantic import BaseModel
from uuid import UUID
from app.schemas.product import ProductResponse


class WishlistItemResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    product_id: UUID
    product: ProductResponse


class WishlistResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    items: list[WishlistItemResponse]


class AddToWishlist(BaseModel):
    product_id: UUID
