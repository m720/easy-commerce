from sqlalchemy.orm import Session
from app.services.email_service import send_email
from app.config import settings


def order_placed(order, db: Session) -> None:
    if not order.user:
        return
    send_email(
        to=order.user.email,
        subject=f"Order #{order.id} Confirmed",
        body=f"<p>Thank you for your order! Your order <strong>#{order.id}</strong> has been placed successfully.</p>"
             f"<p>Total: <strong>${order.total_amount}</strong></p>",
    )


def order_status_changed(order, db: Session) -> None:
    if not order.user:
        return
    send_email(
        to=order.user.email,
        subject=f"Order #{order.id} Status Update",
        body=f"<p>Your order <strong>#{order.id}</strong> status has been updated to <strong>{order.status.value}</strong>.</p>",
    )


def return_request_updated(return_request, db: Session) -> None:
    if not return_request.user:
        return
    send_email(
        to=return_request.user.email,
        subject=f"Return Request #{return_request.id} Update",
        body=f"<p>Your return request has been <strong>{return_request.status.value}</strong>.</p>"
             + (f"<p>Notes: {return_request.admin_notes}</p>" if return_request.admin_notes else ""),
    )


def low_stock_alert(variant_name: str, sku: str, stock: int, db: Session) -> None:
    if not settings.ADMIN_EMAIL:
        return
    send_email(
        to=settings.ADMIN_EMAIL,
        subject="Low Stock Alert",
        body=f"<p>Variant <strong>{variant_name}</strong> (SKU: {sku}) is low on stock: <strong>{stock}</strong> remaining.</p>",
    )
