from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.coupon import Coupon
from app.core.enums import CouponType


def validate_coupon(code: str, order_subtotal: Decimal, db: Session) -> tuple[Coupon, Decimal]:
    coupon = db.query(Coupon).filter(Coupon.code == code).first()
    if not coupon:
        raise HTTPException(status_code=400, detail="Coupon not found")
    if not coupon.is_active:
        raise HTTPException(status_code=400, detail="Coupon is inactive")
    if coupon.expires_at and coupon.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Coupon has expired")
    if coupon.max_uses is not None and coupon.used_count >= coupon.max_uses:
        raise HTTPException(status_code=400, detail="Coupon usage limit reached")
    if coupon.min_order_amount is not None and order_subtotal < coupon.min_order_amount:
        raise HTTPException(
            status_code=400,
            detail=f"Minimum order amount is {coupon.min_order_amount}",
        )

    if coupon.type == CouponType.percent:
        discount = (order_subtotal * Decimal(str(coupon.value)) / Decimal("100")).quantize(Decimal("0.01"))
    else:
        discount = min(Decimal(str(coupon.value)), order_subtotal)

    return coupon, discount


def increment_coupon_usage(coupon: Coupon, db: Session) -> None:
    coupon.used_count += 1
    db.add(coupon)
