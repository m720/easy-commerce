import csv
import io
from datetime import date
from decimal import Decimal
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from app.models.order import Order, OrderItem
from app.models.product import Product, ProductVariant
from app.models.user import User
from app.models.coupon import Coupon
from app.core.enums import OrderStatus


def revenue(db: Session, from_date: Optional[date] = None, to_date: Optional[date] = None) -> dict:
    q = db.query(func.sum(Order.total_amount)).filter(Order.status != OrderStatus.cancelled)
    if from_date:
        q = q.filter(Order.created_at >= from_date)
    if to_date:
        q = q.filter(Order.created_at <= to_date)
    total = q.scalar() or Decimal("0")
    return {"total_revenue": float(total)}


def orders_by_status(db: Session) -> list:
    rows = db.query(Order.status, func.count(Order.id)).group_by(Order.status).all()
    return [{"status": r[0].value, "count": r[1]} for r in rows]


def top_products(db: Session, limit: int = 10) -> list:
    rows = (
        db.query(
            OrderItem.product_name,
            func.sum(OrderItem.quantity).label("total_sold"),
            func.sum(OrderItem.subtotal).label("total_revenue"),
        )
        .group_by(OrderItem.product_name)
        .order_by(desc("total_sold"))
        .limit(limit)
        .all()
    )
    return [{"product_name": r[0], "total_sold": r[1], "total_revenue": float(r[2])} for r in rows]


def top_variants(db: Session, limit: int = 10) -> list:
    rows = (
        db.query(
            OrderItem.variant_name,
            func.sum(OrderItem.quantity).label("total_sold"),
        )
        .group_by(OrderItem.variant_name)
        .order_by(desc("total_sold"))
        .limit(limit)
        .all()
    )
    return [{"variant_name": r[0], "total_sold": r[1]} for r in rows]


def user_stats(db: Session, from_date: Optional[date] = None, to_date: Optional[date] = None) -> dict:
    total = db.query(func.count(User.id)).scalar()
    q = db.query(func.count(User.id))
    if from_date:
        q = q.filter(User.created_at >= from_date)
    if to_date:
        q = q.filter(User.created_at <= to_date)
    new_users = q.scalar()
    return {"total_users": total, "new_users_in_period": new_users}


def average_order_value(db: Session) -> dict:
    avg = db.query(func.avg(Order.total_amount)).filter(Order.status != OrderStatus.cancelled).scalar()
    return {"average_order_value": float(avg or 0)}


def coupon_stats(db: Session) -> list:
    rows = db.query(Coupon.code, Coupon.used_count, Coupon.max_uses).all()
    return [{"code": r[0], "used_count": r[1], "max_uses": r[2]} for r in rows]


def summary(db: Session) -> dict:
    return {
        **revenue(db),
        "orders_by_status": orders_by_status(db),
        **average_order_value(db),
        **user_stats(db),
    }


def low_stock_items(db: Session) -> list:
    variants = (
        db.query(ProductVariant)
        .filter(ProductVariant.stock_quantity <= ProductVariant.low_stock_threshold)
        .all()
    )
    return [
        {
            "variant_id": str(v.id),
            "sku": v.sku,
            "name": v.name,
            "stock_quantity": v.stock_quantity,
            "low_stock_threshold": v.low_stock_threshold,
        }
        for v in variants
    ]


def export_csv(report: str, db: Session) -> str:
    output = io.StringIO()
    writer = csv.writer(output)

    if report == "revenue":
        data = orders_by_status(db)
        writer.writerow(["status", "count"])
        for row in data:
            writer.writerow([row["status"], row["count"]])

    elif report == "top-products":
        data = top_products(db)
        writer.writerow(["product_name", "total_sold", "total_revenue"])
        for row in data:
            writer.writerow([row["product_name"], row["total_sold"], row["total_revenue"]])

    elif report == "top-variants":
        data = top_variants(db)
        writer.writerow(["variant_name", "total_sold"])
        for row in data:
            writer.writerow([row["variant_name"], row["total_sold"]])

    elif report == "coupons":
        data = coupon_stats(db)
        writer.writerow(["code", "used_count", "max_uses"])
        for row in data:
            writer.writerow([row["code"], row["used_count"], row["max_uses"]])

    elif report == "low-stock":
        data = low_stock_items(db)
        writer.writerow(["variant_id", "sku", "name", "stock_quantity", "low_stock_threshold"])
        for row in data:
            writer.writerow([row["variant_id"], row["sku"], row["name"], row["stock_quantity"], row["low_stock_threshold"]])

    else:
        writer.writerow(["error"])
        writer.writerow([f"Unknown report: {report}"])

    return output.getvalue()
