from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from decimal import Decimal
from datetime import datetime
from app.core.enums import OrderStatus, ReturnStatus


class OrderItemResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    variant_id: Optional[UUID]
    product_name: str
    variant_name: str
    unit_price: Decimal
    quantity: int
    subtotal: Decimal


class OrderResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    user_id: Optional[UUID]
    status: OrderStatus
    total_amount: Decimal
    discount_amount: Decimal
    coupon_id: Optional[UUID]
    shipping_address_snapshot: Optional[dict]
    created_at: datetime
    items: List[OrderItemResponse]


class PlaceOrderRequest(BaseModel):
    address_id: UUID
    coupon_code: Optional[str] = None


class UpdateOrderStatus(BaseModel):
    status: OrderStatus


class ReturnRequestItemIn(BaseModel):
    order_item_id: UUID
    quantity: int


class ReturnRequestCreate(BaseModel):
    reason: str
    items: List[ReturnRequestItemIn]


class ReturnRequestItemResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    order_item_id: UUID
    quantity: int


class ReturnRequestResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    order_id: UUID
    user_id: UUID
    reason: str
    status: ReturnStatus
    admin_notes: Optional[str]
    created_at: datetime
    items: List[ReturnRequestItemResponse]


class ReturnDecision(BaseModel):
    admin_notes: Optional[str] = None
