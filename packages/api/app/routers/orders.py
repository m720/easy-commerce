from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from datetime import date
from app.dependencies import get_db, get_current_user, require_admin, Pagination
from app.models.order import Order, ReturnRequest, ReturnRequestItem
from app.schemas.order import (
    OrderResponse, PlaceOrderRequest, UpdateOrderStatus,
    ReturnRequestCreate, ReturnRequestResponse, ReturnDecision,
)
from app.services import order_service
from app.services import notification_service
from app.core.enums import OrderStatus, ReturnStatus

router = APIRouter(prefix="/orders", tags=["Orders"])


# --- User endpoints ---

@router.post("", response_model=OrderResponse, status_code=201)
def place_order(
    data: PlaceOrderRequest,
    background_tasks: BackgroundTasks,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return order_service.place_order(current_user, data.address_id, data.coupon_code, db, background_tasks)


@router.get("", response_model=List[OrderResponse])
def my_orders(pagination: Pagination = Depends(), current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    return (
        db.query(Order)
        .filter(Order.user_id == current_user.id)
        .order_by(Order.created_at.desc())
        .offset(pagination.skip)
        .limit(pagination.limit)
        .all()
    )


@router.get("/{order_id}", response_model=OrderResponse)
def get_order(order_id: UUID, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id, Order.user_id == current_user.id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.delete("/{order_id}", status_code=204)
def cancel_order(order_id: UUID, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    order_service.cancel_order(order_id, current_user, db)


# --- Admin endpoints ---

@router.get("/admin/all", response_model=List[OrderResponse])
def admin_list_orders(
    status: Optional[OrderStatus] = Query(None),
    user_id: Optional[UUID] = Query(None),
    from_date: Optional[date] = Query(None),
    to_date: Optional[date] = Query(None),
    pagination: Pagination = Depends(),
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    q = db.query(Order)
    if status:
        q = q.filter(Order.status == status)
    if user_id:
        q = q.filter(Order.user_id == user_id)
    if from_date:
        q = q.filter(Order.created_at >= from_date)
    if to_date:
        q = q.filter(Order.created_at <= to_date)
    return q.order_by(Order.created_at.desc()).offset(pagination.skip).limit(pagination.limit).all()


@router.patch("/admin/{order_id}/status", response_model=OrderResponse)
def admin_update_status(
    order_id: UUID,
    data: UpdateOrderStatus,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    return order_service.admin_update_status(order_id, data.status, db, background_tasks)


# --- Return Requests ---

@router.post("/{order_id}/returns", response_model=ReturnRequestResponse, status_code=201)
def submit_return(
    order_id: UUID,
    data: ReturnRequestCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    order = db.query(Order).filter(Order.id == order_id, Order.user_id == current_user.id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.status != OrderStatus.delivered:
        raise HTTPException(status_code=400, detail="Returns only allowed for delivered orders")

    rr = ReturnRequest(order_id=order_id, user_id=current_user.id, reason=data.reason)
    db.add(rr)
    db.flush()

    for item_in in data.items:
        rri = ReturnRequestItem(
            return_request_id=rr.id,
            order_item_id=item_in.order_item_id,
            quantity=item_in.quantity,
        )
        db.add(rri)

    db.commit()
    db.refresh(rr)
    return rr


@router.get("/{order_id}/returns/{return_id}", response_model=ReturnRequestResponse)
def get_return(order_id: UUID, return_id: UUID, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    rr = db.query(ReturnRequest).filter(
        ReturnRequest.id == return_id,
        ReturnRequest.order_id == order_id,
        ReturnRequest.user_id == current_user.id,
    ).first()
    if not rr:
        raise HTTPException(status_code=404, detail="Return request not found")
    return rr


# --- Admin Return endpoints ---

@router.get("/admin/returns", response_model=List[ReturnRequestResponse])
def admin_list_returns(pagination: Pagination = Depends(), db: Session = Depends(get_db), _=Depends(require_admin)):
    return db.query(ReturnRequest).order_by(ReturnRequest.created_at.desc()).offset(pagination.skip).limit(pagination.limit).all()


@router.patch("/admin/returns/{return_id}/approve", response_model=ReturnRequestResponse)
def approve_return(
    return_id: UUID,
    data: ReturnDecision,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    rr = db.query(ReturnRequest).filter(ReturnRequest.id == return_id).first()
    if not rr:
        raise HTTPException(status_code=404, detail="Return request not found")
    rr.status = ReturnStatus.approved
    rr.admin_notes = data.admin_notes
    rr.order.status = OrderStatus.returned
    db.commit()
    db.refresh(rr)
    background_tasks.add_task(notification_service.return_request_updated, rr, db)
    return rr


@router.patch("/admin/returns/{return_id}/reject", response_model=ReturnRequestResponse)
def reject_return(
    return_id: UUID,
    data: ReturnDecision,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    rr = db.query(ReturnRequest).filter(ReturnRequest.id == return_id).first()
    if not rr:
        raise HTTPException(status_code=404, detail="Return request not found")
    rr.status = ReturnStatus.rejected
    rr.admin_notes = data.admin_notes
    db.commit()
    db.refresh(rr)
    background_tasks.add_task(notification_service.return_request_updated, rr, db)
    return rr
