from decimal import Decimal
from uuid import UUID
from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, BackgroundTasks
from app.core import metrics
from app.core.logging import get_logger
from app.models.cart import Cart, CartItem
from app.models.order import Order, OrderItem
from app.models.product import ProductVariant
from app.models.address import Address
from app.core.enums import OrderStatus
from app.services.cart_service import get_or_create_cart, clear_cart
from app.services.coupon_service import validate_coupon, increment_coupon_usage
from app.services import notification_service

logger = get_logger("app.orders")


def _reject(reason: str, status_code: int, detail: str) -> HTTPException:
    """Count a checkout rejection before raising it.

    Reasons are a closed set so `order_placement_failures_total` stays a usable
    dashboard series: a spike in `insufficient_stock` is an inventory problem,
    a spike in `coupon_invalid` is usually a broken campaign.
    """
    if metrics.enabled():
        metrics.order_placement_failures_total.labels(reason=reason).inc()
    logger.warning("checkout rejected", extra={"reason": reason, "detail": detail})
    return HTTPException(status_code=status_code, detail=detail)


def place_order(user, address_id: UUID, coupon_code: str | None, db: Session, background_tasks: BackgroundTasks) -> Order:
    logger.info(
        "checkout started",
        extra={"user_id": str(user.id), "address_id": str(address_id), "coupon_code": coupon_code},
    )

    # Validate shipping address
    address = db.query(Address).filter(Address.id == address_id, Address.user_id == user.id).first()
    if not address:
        raise _reject("address_not_found", 404, "Address not found")

    cart = get_or_create_cart(user.id, db)
    if not cart.items:
        raise _reject("empty_cart", 400, "Cart is empty")

    # Collect variant IDs
    variant_ids = [item.variant_id for item in cart.items]

    # SELECT FOR UPDATE — acquire row-level locks on all variants atomically.
    # Ordered by ID so concurrent checkouts touching overlapping carts always
    # take locks in the same sequence and cannot deadlock each other.
    variants = (
        db.query(ProductVariant)
        .filter(ProductVariant.id.in_(variant_ids))
        .options(joinedload(ProductVariant.product))
        .order_by(ProductVariant.id)
        .with_for_update(of=ProductVariant)
        .all()
    )
    variant_map = {v.id: v for v in variants}

    # Validate stock
    cart_item_map = {item.variant_id: item for item in cart.items}
    for vid, item in cart_item_map.items():
        variant = variant_map.get(vid)
        if not variant:
            raise _reject("variant_missing", 400, f"Variant {vid} not found")
        if variant.stock_quantity < item.quantity:
            raise _reject(
                "insufficient_stock",
                400,
                f"Insufficient stock for {variant.name} (available: {variant.stock_quantity})",
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
        try:
            coupon, discount_amount = validate_coupon(coupon_code, subtotal, db)
        except HTTPException as exc:
            if metrics.enabled():
                metrics.order_placement_failures_total.labels(reason="coupon_invalid").inc()
            logger.warning(
                "checkout rejected",
                extra={"reason": "coupon_invalid", "detail": str(exc.detail), "coupon_code": coupon_code},
            )
            raise

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

    # Clear the cart inside the same transaction: order write, stock decrement
    # and cart clear commit together or not at all.
    clear_cart(cart, db, commit=False)

    db.commit()
    db.refresh(order)

    if metrics.enabled():
        metrics.orders_placed_total.inc()
    logger.info(
        "order placed",
        extra={
            "order_id": str(order.id),
            "user_id": str(user.id),
            "total_amount": str(order.total_amount),
            "discount_amount": str(order.discount_amount),
            "item_count": len(order.items),
            "low_stock_variants": len(low_stock_variants),
        },
    )

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
    logger.info("order cancelled", extra={"order_id": str(order.id), "user_id": str(user.id)})
    return order


def admin_update_status(order_id: UUID, new_status: OrderStatus, db: Session, background_tasks: BackgroundTasks) -> Order:
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    previous_status = order.status
    order.status = new_status
    db.commit()
    db.refresh(order)
    logger.info(
        "order status changed",
        extra={
            "order_id": str(order.id),
            "previous_status": previous_status.value if previous_status else None,
            "new_status": new_status.value,
        },
    )
    background_tasks.add_task(notification_service.order_status_changed, order, db)
    return order
