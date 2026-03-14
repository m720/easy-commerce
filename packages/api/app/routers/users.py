from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from app.dependencies import get_db, require_admin, Pagination
from app.models.user import User
from app.models.wishlist import Wishlist, WishlistItem
from app.schemas.auth import UserResponse
from app.schemas.user import UserActivitySummary

router = APIRouter(prefix="/users", tags=["Users (Admin)"])


@router.get("", response_model=List[UserResponse])
def list_users(
    pagination: Pagination = Depends(),
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    return db.query(User).offset(pagination.skip).limit(pagination.limit).all()


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: UUID, db: Session = Depends(get_db), _=Depends(require_admin)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.patch("/{user_id}/activate", response_model=UserResponse)
def activate_user(user_id: UUID, db: Session = Depends(get_db), _=Depends(require_admin)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = True
    db.commit()
    db.refresh(user)
    return user


@router.patch("/{user_id}/deactivate", response_model=UserResponse)
def deactivate_user(user_id: UUID, db: Session = Depends(get_db), _=Depends(require_admin)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = False
    db.commit()
    db.refresh(user)
    return user


@router.get("/{user_id}/activity", response_model=UserActivitySummary)
def user_activity(user_id: UUID, db: Session = Depends(get_db), _=Depends(require_admin)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    total_orders = user.orders.count()
    total_reviews = user.reviews.count()

    wishlist = db.query(Wishlist).filter(Wishlist.user_id == user_id).first()
    wishlist_count = 0
    if wishlist:
        wishlist_count = db.query(WishlistItem).filter(WishlistItem.wishlist_id == wishlist.id).count()

    return UserActivitySummary(
        user=UserResponse.model_validate(user),
        total_orders=total_orders,
        total_reviews=total_reviews,
        wishlist_items=wishlist_count,
    )
