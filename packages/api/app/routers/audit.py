from datetime import date
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.dependencies import Pagination, get_db, require_admin
from app.models.audit import AuditLog
from app.schemas.audit import AuditLogResponse

router = APIRouter(prefix="/audit-logs", tags=["Audit (Admin)"])


@router.get("", response_model=List[AuditLogResponse])
def list_audit_logs(
    action: Optional[str] = Query(None, description="Exact action name, e.g. product.updated"),
    entity_type: Optional[str] = Query(None),
    entity_id: Optional[str] = Query(None),
    actor_user_id: Optional[UUID] = Query(None),
    from_date: Optional[date] = Query(None),
    to_date: Optional[date] = Query(None),
    pagination: Pagination = Depends(),
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    """Read the admin audit trail, newest first.

    Read-only by design: there is no endpoint to edit or delete entries, which
    is the point of an audit log. Retention is handled out-of-band (partition
    drop or archival), not by the API.
    """
    q = db.query(AuditLog)
    if action:
        q = q.filter(AuditLog.action == action)
    if entity_type:
        q = q.filter(AuditLog.entity_type == entity_type)
    if entity_id:
        q = q.filter(AuditLog.entity_id == str(entity_id))
    if actor_user_id:
        q = q.filter(AuditLog.actor_user_id == actor_user_id)
    if from_date:
        q = q.filter(AuditLog.created_at >= from_date)
    if to_date:
        q = q.filter(AuditLog.created_at <= to_date)
    return (
        q.order_by(AuditLog.created_at.desc())
        .offset(pagination.skip)
        .limit(pagination.limit)
        .all()
    )
