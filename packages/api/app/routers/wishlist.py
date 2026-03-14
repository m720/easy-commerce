from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from app.dependencies import get_db, get_current_user
from app.models.wishlist import Wishlist, WishlistItem
from app.models.cart import Cart, CartItem
from app.schemas.wishlist import WishlistResponse, AddToWishlist
from app.services.cart_service import get_or_create_cart

router = APIRouter(prefix="/wishlist", tags=["Wishlist"])


def get_or_create_wishlist(user_id: UUID, db: Session) -> Wishlist:
    wishlist = db.query(Wishlist).filter(Wishlist.user_id == user_id).first()
    if not wishlist:
        wishlist = Wishlist(user_id=user_id)
        db.add(wishlist)
        db.commit()
        db.refresh(wishlist)
    return wishlist


@router.get("", response_model=WishlistResponse)
def get_wishlist(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    wishlist = get_or_create_wishlist(current_user.id, db)
    db.refresh(wishlist)
    return wishlist


@router.post("", status_code=201)
def add_to_wishlist(data: AddToWishlist, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    wishlist = get_or_create_wishlist(current_user.id, db)
    existing = db.query(WishlistItem).filter(
        WishlistItem.wishlist_id == wishlist.id,
        WishlistItem.product_id == data.product_id,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Product already in wishlist")
    item = WishlistItem(wishlist_id=wishlist.id, product_id=data.product_id)
    db.add(item)
    db.commit()
    return {"message": "Added to wishlist"}


@router.delete("/{item_id}", status_code=204)
def remove_from_wishlist(item_id: UUID, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    wishlist = get_or_create_wishlist(current_user.id, db)
    item = db.query(WishlistItem).filter(WishlistItem.id == item_id, WishlistItem.wishlist_id == wishlist.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    db.delete(item)
    db.commit()


@router.post("/{item_id}/move-to-cart")
def move_to_cart(item_id: UUID, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    wishlist = get_or_create_wishlist(current_user.id, db)
    item = db.query(WishlistItem).filter(WishlistItem.id == item_id, WishlistItem.wishlist_id == wishlist.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    # Get the first available variant
    from app.models.product import ProductVariant
    variant = db.query(ProductVariant).filter(
        ProductVariant.product_id == item.product_id,
        ProductVariant.stock_quantity > 0,
    ).first()
    if not variant:
        raise HTTPException(status_code=400, detail="No available variant in stock")

    cart = get_or_create_cart(current_user.id, db)
    cart_item = db.query(CartItem).filter(CartItem.cart_id == cart.id, CartItem.variant_id == variant.id).first()
    if cart_item:
        cart_item.quantity += 1
    else:
        cart_item = CartItem(cart_id=cart.id, variant_id=variant.id, quantity=1)
        db.add(cart_item)

    db.delete(item)
    db.commit()
    return {"message": "Moved to cart"}
