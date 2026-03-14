from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date
import io
from app.dependencies import get_db, require_admin
from app.services import analytics_service

router = APIRouter(prefix="/analytics", tags=["Analytics (Admin)"])


@router.get("/revenue")
def get_revenue(
    from_date: Optional[date] = Query(None),
    to_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    return analytics_service.revenue(db, from_date, to_date)


@router.get("/orders")
def get_orders_by_status(db: Session = Depends(get_db), _=Depends(require_admin)):
    return analytics_service.orders_by_status(db)


@router.get("/top-products")
def get_top_products(limit: int = Query(default=10, ge=1, le=50), db: Session = Depends(get_db), _=Depends(require_admin)):
    return analytics_service.top_products(db, limit)


@router.get("/top-variants")
def get_top_variants(limit: int = Query(default=10, ge=1, le=50), db: Session = Depends(get_db), _=Depends(require_admin)):
    return analytics_service.top_variants(db, limit)


@router.get("/users")
def get_user_stats(
    from_date: Optional[date] = Query(None),
    to_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    return analytics_service.user_stats(db, from_date, to_date)


@router.get("/aov")
def get_aov(db: Session = Depends(get_db), _=Depends(require_admin)):
    return analytics_service.average_order_value(db)


@router.get("/coupons")
def get_coupon_stats(db: Session = Depends(get_db), _=Depends(require_admin)):
    return analytics_service.coupon_stats(db)


@router.get("/summary")
def get_summary(db: Session = Depends(get_db), _=Depends(require_admin)):
    return analytics_service.summary(db)


@router.get("/low-stock")
def get_low_stock(db: Session = Depends(get_db), _=Depends(require_admin)):
    return analytics_service.low_stock_items(db)


@router.get("/export/{report}.csv")
def export_csv(report: str, db: Session = Depends(get_db), _=Depends(require_admin)):
    content = analytics_service.export_csv(report, db)
    return StreamingResponse(
        io.StringIO(content),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={report}.csv"},
    )
