from decimal import Decimal
from uuid import UUID
from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, BackgroundTasks
from app.models.cart import Cart, CartItem
from app.models.order import Order, OrderItem
from app.models.product import ProductVariant
from app.models.address import Address
from app.core.enums import OrderStatus
from app.services.cart_service import get_or_create_cart, clear_cart
from app.services.coupon_service import validate_coupon, increment_coupon_usage
from app.services import notification_service


def place_order(user, address_id: UUID, coupon_code: str | None, db: Session, background_tasks: BackgroundTasks) -> Order:
    # Validate shipping address
    address = db.query(Address).filter(Address.id == address_id, Address.user_id == user.id).first()
    if not address:
        raise HTTPException(status_code=404, detail="Address not found")

    cart = get_or_create_cart(user.id, db)
    if not cart.items:
        raise HTTPException(status_code=400, detail="Cart is empty")

    # Collect variant IDs
    variant_ids = [item.variant_id for item in cart.items]

    # SELECT FOR UPDATE — acquire row-level locks on all variants atomically
    variants = (
        db.query(ProductVariant)
        .filter(ProductVariant.id.in_(variant_ids))
        .options(joinedload(ProductVariant.product))
        .with_for_update()
        .all()
    )
    variant_map = {v.id: v for v in variants}

    # Validate stock
    cart_item_map = {item.variant_id: item for item in cart.items}
    for vid, item in cart_item_map.items():
        variant = variant_map.get(vid)
        if not variant:
            raise HTTPException(status_code=400, detail=f"Variant {vid} not found")
        if variant.stock_quantity < item.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient stock for {variant.name} (available: {variant.stock_quantity})",
            )

    # Compute subtotal
    subtotal = sum(
        Decimal(str(variant_map[item.variant_id].price)) * item.quantity
        for item in cart.items
    )

    # Apply coupon
    coupon = None
    discount_amount = Decimal("0")
    if coupon_code:
        coupon, discount_amount = validate_coupon(coupon_code, subtotal, db)

    total = subtotal - discount_amount

    # Build shipping address snapshot
    address_snapshot = {
        "label": address.label,
        "street": address.street,
        "city": address.city,
        "state": address.state,
        "country": address.country,
        "postal_code": address.postal_code,
    }

    # Create order
    order = Order(
        user_id=user.id,
        status=OrderStatus.pending,
        total_amount=total,
        discount_amount=discount_amount,
        coupon_id=coupon.id if coupon else None,
        shipping_address_snapshot=address_snapshot,
    )
    db.add(order)
    db.flush()  # get order.id without committing

    # Create order items + decrement stock + check low-stock
    low_stock_variants = []
    for item in cart.items:
        variant = variant_map[item.variant_id]
        order_item = OrderItem(
            order_id=order.id,
            variant_id=variant.id,
            product_name=variant.product.name,
            variant_name=variant.name,
            unit_price=variant.price,
            quantity=item.quantity,
            subtotal=Decimal(str(variant.price)) * item.quantity,
        )
        db.add(order_item)

        # Decrement stock
        variant.stock_quantity -= item.quantity

        # Check low-stock threshold
        if variant.stock_quantity <= variant.low_stock_threshold:
            low_stock_variants.append(variant)

    # Track coupon usage
    if coupon:
        increment_coupon_usage(coupon, db)

    # Clear cart
    clear_cart(cart, db)

    db.commit()
    db.refresh(order)

    # Trigger notifications in background
    background_tasks.add_task(notification_service.order_placed, order, db)
    for v in low_stock_variants:
        background_tasks.add_task(notification_service.low_stock_alert, v.name, v.sku, v.stock_quantity, db)

    return order


def cancel_order(order_id: UUID, user, db: Session) -> Order:
    order = db.query(Order).filter(Order.id == order_id, Order.user_id == user.id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.status != OrderStatus.pending:
        raise HTTPException(status_code=400, detail="Only pending orders can be cancelled")
    order.status = OrderStatus.cancelled
    db.commit()
    db.refresh(order)
    return order


def admin_update_status(order_id: UUID, new_status: OrderStatus, db: Session, background_tasks: BackgroundTasks) -> Order:
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    order.status = new_status
    db.commit()
    db.refresh(order)
    background_tasks.add_task(notification_service.order_status_changed, order, db)
    return order
