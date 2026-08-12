"""Audit trail for privileged actions.

Answers questions incident reviews actually ask: who changed this price, who
approved this return, who deactivated this account, and when.

Two rules shape the implementation:

* **Auditing never breaks the action it audits.** A failure to write the trail
  is logged and swallowed; an admin does not get a 500 because the audit insert
  hit a constraint. (Regulated environments invert this — there the audit write
  is part of the transaction and a failure aborts the action. Noted in the ADR.)
* **Record the diff, not the document.** Storing only changed fields keeps rows
  small and makes "what actually changed" readable without diffing two blobs.
"""

from decimal import Decimal
from enum import Enum
from typing import Any, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.core import metrics
from app.core.logging import get_logger, get_request_id
from app.models.audit import AuditLog

logger = get_logger("app.audit")


# --- Action names. Constants, not free-form strings, so the set stays greppable
# and dashboards can rely on stable labels. ---

class AuditAction:
    PRODUCT_CREATED = "product.created"
    PRODUCT_UPDATED = "product.updated"
    PRODUCT_DELETED = "product.deleted"
    PRODUCT_FEATURED_TOGGLED = "product.featured_toggled"
    PRODUCT_BULK_ACTIVATION = "product.bulk_activation"
    VARIANT_CREATED = "variant.created"
    VARIANT_UPDATED = "variant.updated"
    VARIANT_DELETED = "variant.deleted"
    COUPON_CREATED = "coupon.created"
    COUPON_UPDATED = "coupon.updated"
    COUPON_DELETED = "coupon.deleted"
    ORDER_STATUS_CHANGED = "order.status_changed"
    RETURN_APPROVED = "return.approved"
    RETURN_REJECTED = "return.rejected"
    USER_ACTIVATED = "user.activated"
    USER_DEACTIVATED = "user.deactivated"


def _jsonable(value: Any) -> Any:
    if isinstance(value, (Decimal, UUID)):
        return str(value)
    if isinstance(value, Enum):
        return value.value
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


def diff(before: dict, after: dict) -> dict:
    """Return ``{field: {"before": x, "after": y}}`` for changed fields only."""
    changes: dict[str, dict[str, Any]] = {}
    for field, new_value in after.items():
        old_value = before.get(field)
        if _jsonable(old_value) != _jsonable(new_value):
            changes[field] = {
                "before": _jsonable(old_value),
                "after": _jsonable(new_value),
            }
    return changes


def snapshot(obj: Any, fields: tuple[str, ...]) -> dict:
    """Capture selected attributes of an ORM object for later diffing."""
    return {field: getattr(obj, field, None) for field in fields}


def _normalise_changes(changes: Optional[dict]) -> Optional[dict]:
    """Coerce a changes dict into something JSONB can store.

    Model attributes arrive as Decimal, datetime and Enum values, none of which
    the JSON serialiser accepts. Normalising here — rather than trusting every
    call site to remember — keeps a price change from failing its own audit
    entry.
    """
    if not changes:
        return None

    normalised: dict[str, Any] = {}
    for field, value in changes.items():
        if isinstance(value, dict):
            normalised[field] = {k: _jsonable(v) for k, v in value.items()}
        elif isinstance(value, (list, tuple)):
            normalised[field] = [_jsonable(v) for v in value]
        else:
            normalised[field] = _jsonable(value)
    return normalised or None


def record(
    db: Session,
    *,
    action: str,
    entity_type: str,
    entity_id: Optional[Any] = None,
    entity_label: Optional[str] = None,
    changes: Optional[dict] = None,
    actor: Optional[Any] = None,
    ip_address: Optional[str] = None,
    commit: bool = True,
) -> Optional[AuditLog]:
    try:
        entry = AuditLog(
            actor_user_id=getattr(actor, "id", None),
            actor_email=getattr(actor, "email", None),
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id) if entity_id is not None else None,
            entity_label=entity_label,
            changes=_normalise_changes(changes),
            request_id=get_request_id(),
            ip_address=ip_address,
        )
        db.add(entry)
        if commit:
            db.commit()
        else:
            db.flush()

        if metrics.enabled():
            metrics.audit_events_total.labels(action=action).inc()

        logger.info(
            "admin action recorded",
            extra={
                "audit_action": action,
                "entity_type": entity_type,
                "entity_id": str(entity_id) if entity_id is not None else None,
                "actor_email": getattr(actor, "email", None),
            },
        )
        return entry
    except Exception as exc:  # noqa: BLE001
        # The business action already succeeded; losing its audit row is worth
        # an alertable error log, not a failed request for the admin.
        logger.error(
            "failed to write audit log",
            extra={"audit_action": action, "error": str(exc)},
            exc_info=True,
        )
        try:
            db.rollback()
        except Exception:  # noqa: BLE001
            pass
        return None


class AuditContext:
    """Request-scoped helper handed to admin routes by dependency injection.

    Carries the actor and client IP so call sites only state *what* changed.
    """

    def __init__(self, actor: Any, ip_address: Optional[str]):
        self.actor = actor
        self.ip_address = ip_address

    def record(self, db: Session, **kwargs) -> Optional[AuditLog]:
        kwargs.setdefault("actor", self.actor)
        kwargs.setdefault("ip_address", self.ip_address)
        return record(db, **kwargs)
