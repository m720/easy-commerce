from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from app.dependencies import get_db, get_current_user, require_admin, Pagination
from app.models.coupon import Coupon
from app.schemas.coupon import CouponCreate, CouponUpdate, CouponResponse, CouponValidateRequest, CouponValidateResponse
from app.services.coupon_service import validate_coupon

router = APIRouter(prefix="/coupons", tags=["Coupons"])


@router.post("/validate", response_model=CouponValidateResponse)
def validate(data: CouponValidateRequest, _=Depends(get_current_user), db: Session = Depends(get_db)):
    coupon, discount = validate_coupon(data.code, data.order_subtotal, db)
    return {"valid": True, "discount_amount": discount, "coupon": coupon}


# Admin endpoints

@router.get("", response_model=List[CouponResponse])
def list_coupons(pagination: Pagination = Depends(), db: Session = Depends(get_db), _=Depends(require_admin)):
    return db.query(Coupon).offset(pagination.skip).limit(pagination.limit).all()


@router.post("", response_model=CouponResponse, status_code=201)
def create_coupon(data: CouponCreate, db: Session = Depends(get_db), _=Depends(require_admin)):
    if db.query(Coupon).filter(Coupon.code == data.code).first():
        raise HTTPException(status_code=400, detail="Coupon code already exists")
    coupon = Coupon(**data.model_dump())
    db.add(coupon)
    db.commit()
    db.refresh(coupon)
    return coupon


@router.put("/{coupon_id}", response_model=CouponResponse)
def update_coupon(coupon_id: UUID, data: CouponUpdate, db: Session = Depends(get_db), _=Depends(require_admin)):
    coupon = db.query(Coupon).filter(Coupon.id == coupon_id).first()
    if not coupon:
        raise HTTPException(status_code=404, detail="Coupon not found")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(coupon, k, v)
    db.commit()
    db.refresh(coupon)
    return coupon


@router.delete("/{coupon_id}", status_code=204)
def delete_coupon(coupon_id: UUID, db: Session = Depends(get_db), _=Depends(require_admin)):
    coupon = db.query(Coupon).filter(Coupon.id == coupon_id).first()
    if not coupon:
        raise HTTPException(status_code=404, detail="Coupon not found")
    db.delete(coupon)
    db.commit()
