from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime
from app.core.enums import UserRole
from app.schemas.auth import UserResponse


class UserActivitySummary(BaseModel):
    model_config = {"from_attributes": True}

    user: UserResponse
    total_orders: int
    total_reviews: int
    wishlist_items: int
