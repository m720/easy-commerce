from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime


class ReviewCreate(BaseModel):
    rating: int = Field(ge=1, le=5)
    comment: Optional[str] = None


class ReviewUpdate(BaseModel):
    rating: Optional[int] = Field(default=None, ge=1, le=5)
    comment: Optional[str] = None


class ReviewResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    user_id: UUID
    product_id: UUID
    rating: int
    comment: Optional[str]
    is_approved: bool
    created_at: datetime
