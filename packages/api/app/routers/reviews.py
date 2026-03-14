from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from app.dependencies import get_db, get_current_user, require_admin, Pagination
from app.models.review import Review
from app.schemas.review import ReviewCreate, ReviewUpdate, ReviewResponse

router = APIRouter(prefix="/products/{product_id}/reviews", tags=["Reviews"])


@router.get("", response_model=List[ReviewResponse])
def list_reviews(
    product_id: UUID,
    pagination: Pagination = Depends(),
    sort_by: str = Query(default="created_at", pattern="^(created_at|rating)$"),
    db: Session = Depends(get_db),
):
    q = db.query(Review).filter(Review.product_id == product_id, Review.is_approved == True)
    if sort_by == "rating":
        q = q.order_by(Review.rating.desc())
    else:
        q = q.order_by(Review.created_at.desc())
    return q.offset(pagination.skip).limit(pagination.limit).all()


@router.post("", response_model=ReviewResponse, status_code=201)
def create_review(
    product_id: UUID,
    data: ReviewCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    existing = db.query(Review).filter(Review.user_id == current_user.id, Review.product_id == product_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="You have already reviewed this product")
    review = Review(user_id=current_user.id, product_id=product_id, **data.model_dump())
    db.add(review)
    db.commit()
    db.refresh(review)
    return review


@router.put("/{review_id}", response_model=ReviewResponse)
def update_review(
    product_id: UUID,
    review_id: UUID,
    data: ReviewUpdate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    review = db.query(Review).filter(Review.id == review_id, Review.product_id == product_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    if review.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your review")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(review, k, v)
    db.commit()
    db.refresh(review)
    return review


@router.delete("/{review_id}", status_code=204)
def delete_review(
    product_id: UUID,
    review_id: UUID,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    review = db.query(Review).filter(Review.id == review_id, Review.product_id == product_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    if review.user_id != current_user.id and current_user.role.value != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    db.delete(review)
    db.commit()


@router.patch("/{review_id}/approve", response_model=ReviewResponse)
def approve_review(product_id: UUID, review_id: UUID, db: Session = Depends(get_db), _=Depends(require_admin)):
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    review.is_approved = True
    db.commit()
    db.refresh(review)
    return review


@router.patch("/{review_id}/hide", response_model=ReviewResponse)
def hide_review(product_id: UUID, review_id: UUID, db: Session = Depends(get_db), _=Depends(require_admin)):
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    review.is_approved = False
    db.commit()
    db.refresh(review)
    return review
