from decimal import Decimal
from uuid import UUID
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.cart import Cart, CartItem
from app.models.product import ProductVariant


def get_or_create_cart(user_id: UUID, db: Session) -> Cart:
    cart = db.query(Cart).filter(Cart.user_id == user_id).first()
    if not cart:
        cart = Cart(user_id=user_id)
        db.add(cart)
        db.commit()
        db.refresh(cart)
    return cart


def get_cart_with_stock_check(user_id: UUID, db: Session) -> dict:
    cart = get_or_create_cart(user_id, db)
    subtotal = Decimal("0")
    enriched_items = []
    for item in cart.items:
        in_stock = item.variant.stock_quantity >= item.quantity
        item_total = Decimal(str(item.variant.price)) * item.quantity
        subtotal += item_total
        enriched_items.append({
            "id": item.id,
            "variant_id": item.variant_id,
            "quantity": item.quantity,
            "variant": item.variant,
            "in_stock": in_stock,
        })
    return {"id": cart.id, "items": enriched_items, "subtotal": subtotal}


def add_item(user_id: UUID, variant_id: UUID, quantity: int, db: Session) -> Cart:
    variant = db.query(ProductVariant).filter(ProductVariant.id == variant_id).first()
    if not variant:
        raise HTTPException(status_code=404, detail="Variant not found")
    if variant.stock_quantity < quantity:
        raise HTTPException(status_code=400, detail="Insufficient stock")

    cart = get_or_create_cart(user_id, db)
    item = db.query(CartItem).filter(CartItem.cart_id == cart.id, CartItem.variant_id == variant_id).first()
    if item:
        item.quantity += quantity
    else:
        item = CartItem(cart_id=cart.id, variant_id=variant_id, quantity=quantity)
        db.add(item)
    db.commit()
    db.refresh(cart)
    return cart


def update_item(user_id: UUID, item_id: UUID, quantity: int, db: Session) -> Cart:
    cart = get_or_create_cart(user_id, db)
    item = db.query(CartItem).filter(CartItem.id == item_id, CartItem.cart_id == cart.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Cart item not found")
    if quantity <= 0:
        db.delete(item)
    else:
        if item.variant.stock_quantity < quantity:
            raise HTTPException(status_code=400, detail="Insufficient stock")
        item.quantity = quantity
    db.commit()
    db.refresh(cart)
    return cart


def remove_item(user_id: UUID, item_id: UUID, db: Session) -> None:
    cart = get_or_create_cart(user_id, db)
    item = db.query(CartItem).filter(CartItem.id == item_id, CartItem.cart_id == cart.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Cart item not found")
    db.delete(item)
    db.commit()


def clear_cart(cart: Cart, db: Session) -> None:
    db.query(CartItem).filter(CartItem.cart_id == cart.id).delete()
    db.commit()
