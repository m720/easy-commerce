from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from uuid import UUID
from app.dependencies import get_db, get_current_user
from app.schemas.cart import CartItemAdd, CartItemUpdate, CartResponse
from app.services import cart_service

router = APIRouter(prefix="/cart", tags=["Cart"])


@router.get("", response_model=CartResponse)
def get_cart(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    return cart_service.get_cart_with_stock_check(current_user.id, db)


@router.post("/items", status_code=201)
def add_item(data: CartItemAdd, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    cart_service.add_item(current_user.id, data.variant_id, data.quantity, db)
    return cart_service.get_cart_with_stock_check(current_user.id, db)


@router.put("/items/{item_id}")
def update_item(item_id: UUID, data: CartItemUpdate, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    cart_service.update_item(current_user.id, item_id, data.quantity, db)
    return cart_service.get_cart_with_stock_check(current_user.id, db)


@router.delete("/items/{item_id}", status_code=204)
def remove_item(item_id: UUID, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    cart_service.remove_item(current_user.id, item_id, db)


@router.delete("", status_code=204)
def clear_cart(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    cart = cart_service.get_or_create_cart(current_user.id, db)
    cart_service.clear_cart(cart, db)
