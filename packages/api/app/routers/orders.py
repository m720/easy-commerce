from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Header, Query, Response
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from datetime import date
from app.dependencies import get_db, get_current_user, require_admin, admin_audit, Pagination
from app.models.order import Order, ReturnRequest, ReturnRequestItem
from app.schemas.order import (
    OrderResponse, PlaceOrderRequest, UpdateOrderStatus,
    ReturnRequestCreate, ReturnRequestResponse, ReturnDecision,
)
from app.services import order_service
from app.services import notification_service
from app.services import idempotency_service
from app.services.audit_service import AuditAction, AuditContext
from app.core.enums import OrderStatus, ReturnStatus

router = APIRouter(prefix="/orders", tags=["Orders"])

CHECKOUT_ENDPOINT = "POST /api/v1/orders"


# --- User endpoints ---

@router.post("", response_model=OrderResponse, status_code=201)
def place_order(
    data: PlaceOrderRequest,
    background_tasks: BackgroundTasks,
    response: Response,
    idempotency_key: Optional[str] = Header(
        default=None,
        alias="Idempotency-Key",
        description=(
            "Client-generated key (a UUID is fine) that makes this call safe to "
            "retry. Retrying with the same key returns the original order "
            "instead of placing a second one."
        ),
    ),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Place an order from the caller's cart.

    Retry-safe when the client supplies an ``Idempotency-Key``. Without one the
    call behaves as before — a network retry can create a second order — which
    is why clients should always send it. See
    docs/adr/0003-idempotency-keys-for-checkout.md.
    """
    key = idempotency_service.validate_key(idempotency_key)

    if key is None:
        order = order_service.place_order(
            current_user, data.address_id, data.coupon_code, db, background_tasks
        )
        return order

    fingerprint = idempotency_service.fingerprint(data.model_dump(mode="json"))
    replay = idempotency_service.reserve(
        db,
        key=key,
        user_id=current_user.id,
        endpoint=CHECKOUT_ENDPOINT,
        request_fingerprint=fingerprint,
    )
    if replay is not None:
        # A retry of a completed checkout: hand back the original order,
        # unchanged, with no second write.
        response.status_code = replay.status_code
        response.headers["Idempotency-Replayed"] = "true"
        return replay.body

    try:
        order = order_service.place_order(
            current_user, data.address_id, data.coupon_code, db, background_tasks
        )
    except Exception:
        # The order was not created, so the key must not stay claimed —
        # otherwise a client fixing a bad address would be stuck behind its own
        # in-flight reservation.
        idempotency_service.release(
            db, key=key, user_id=current_user.id, endpoint=CHECKOUT_ENDPOINT
        )
        raise

    body = OrderResponse.model_validate(order).model_dump(mode="json")
    idempotency_service.complete(
        db,
        key=key,
        user_id=current_user.id,
        endpoint=CHECKOUT_ENDPOINT,
        status_code=201,
        body=body,
        entity_id=order.id,
    )
    response.headers["Idempotency-Replayed"] = "false"
    return body


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
    audit: AuditContext = Depends(admin_audit),
):
    previous = db.query(Order.status).filter(Order.id == order_id).scalar()
    order = order_service.admin_update_status(order_id, data.status, db, background_tasks)
    audit.record(
        db,
        action=AuditAction.ORDER_STATUS_CHANGED,
        entity_type="order",
        entity_id=order.id,
        changes={
            "status": {
                "before": previous.value if previous else None,
                "after": order.status.value,
            }
        },
    )
    return order


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
    audit: AuditContext = Depends(admin_audit),
):
    rr = db.query(ReturnRequest).filter(ReturnRequest.id == return_id).first()
    if not rr:
        raise HTTPException(status_code=404, detail="Return request not found")
    previous_status = rr.status
    rr.status = ReturnStatus.approved
    rr.admin_notes = data.admin_notes
    rr.order.status = OrderStatus.returned
    db.commit()
    db.refresh(rr)
    audit.record(
        db,
        action=AuditAction.RETURN_APPROVED,
        entity_type="return_request",
        entity_id=rr.id,
        entity_label=f"order {rr.order_id}",
        changes={
            "status": {"before": previous_status.value, "after": rr.status.value},
            "admin_notes": {"before": None, "after": data.admin_notes},
        },
    )
    background_tasks.add_task(notification_service.return_request_updated, rr, db)
    return rr


@router.patch("/admin/returns/{return_id}/reject", response_model=ReturnRequestResponse)
def reject_return(
    return_id: UUID,
    data: ReturnDecision,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    audit: AuditContext = Depends(admin_audit),
):
    rr = db.query(ReturnRequest).filter(ReturnRequest.id == return_id).first()
    if not rr:
        raise HTTPException(status_code=404, detail="Return request not found")
    previous_status = rr.status
    rr.status = ReturnStatus.rejected
    rr.admin_notes = data.admin_notes
    db.commit()
    db.refresh(rr)
    audit.record(
        db,
        action=AuditAction.RETURN_REJECTED,
        entity_type="return_request",
        entity_id=rr.id,
        entity_label=f"order {rr.order_id}",
        changes={
            "status": {"before": previous_status.value, "after": rr.status.value},
            "admin_notes": {"before": None, "after": data.admin_notes},
        },
    )
    background_tasks.add_task(notification_service.return_request_updated, rr, db)
    return rr
