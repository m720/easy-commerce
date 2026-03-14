from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from decimal import Decimal
from datetime import datetime
from app.core.enums import CouponType


class CouponCreate(BaseModel):
    code: str
    type: CouponType
    value: Decimal
    min_order_amount: Optional[Decimal] = None
    max_uses: Optional[int] = None
    expires_at: Optional[datetime] = None
    is_active: bool = True


class CouponUpdate(BaseModel):
    code: Optional[str] = None
    type: Optional[CouponType] = None
    value: Optional[Decimal] = None
    min_order_amount: Optional[Decimal] = None
    max_uses: Optional[int] = None
    expires_at: Optional[datetime] = None
    is_active: Optional[bool] = None


class CouponResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    code: str
    type: CouponType
    value: Decimal
    min_order_amount: Optional[Decimal]
    max_uses: Optional[int]
    used_count: int
    expires_at: Optional[datetime]
    is_active: bool


class CouponValidateRequest(BaseModel):
    code: str
    order_subtotal: Decimal


class CouponValidateResponse(BaseModel):
    valid: bool
    discount_amount: Decimal
    coupon: CouponResponse
