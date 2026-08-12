"""Idempotent handling of unsafe POSTs (checkout).

The problem: a client sends ``POST /orders``, the order is written, and the
response is lost to a timeout or a dropped connection. The client retries — and
without protection the customer now has two orders and two charges. Retries are
not an edge case; mobile networks guarantee them.

The fix is the industry-standard one (Stripe, Adyen, PayPal all expose it): the
client generates a key, sends it as ``Idempotency-Key``, and the server promises
that a given key produces at most one side effect. A retry replays the stored
response instead of re-executing.

Lifecycle::

    reserve()  ── INSERT (user_id, endpoint, key) ──► in_progress
       │                        │
       │ unique violation       │ handler runs
       ▼                        ▼
    replay stored response   complete() → stored response + order_id
    or 409 if still running  release() on failure → key is retryable

Correctness notes:

* The unique index — not an application-level check — is what makes concurrent
  retries safe. Check-then-insert has a race window; ``INSERT`` does not.
* The reservation is committed *before* the handler runs. A crash mid-checkout
  therefore leaves an ``in_progress`` row, and the retry gets 409 rather than a
  duplicate order. Stale rows past their TTL are reclaimable (see ``purge_expired``).
* A key reused with a *different* body is rejected with 422. Silently returning
  the first response would hide a client bug behind an apparently successful
  order.

See docs/adr/0003-idempotency-keys-for-checkout.md.
"""

import hashlib
import json
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import settings
from app.core import metrics
from app.core.logging import get_logger, get_request_id
from app.models.idempotency import IdempotencyKey

logger = get_logger("app.idempotency")

MAX_KEY_LENGTH = 255
STATUS_IN_PROGRESS = "in_progress"
STATUS_COMPLETED = "completed"


class ReplayedResponse:
    """A previously stored response being served again."""

    def __init__(self, status_code: int, body: Any):
        self.status_code = status_code
        self.body = body


def fingerprint(payload: Any) -> str:
    """Stable SHA-256 over the request body, key order independent."""
    canonical = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def validate_key(key: Optional[str], *, required: Optional[bool] = None) -> Optional[str]:
    """Normalise the header value, enforcing presence only when configured."""
    if required is None:
        required = settings.IDEMPOTENCY_REQUIRED

    if key is None or not key.strip():
        if required:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Idempotency-Key header is required for this endpoint",
            )
        return None

    key = key.strip()
    if len(key) > MAX_KEY_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Idempotency-Key must be at most {MAX_KEY_LENGTH} characters",
        )
    return key


def reserve(
    db: Session,
    *,
    key: str,
    user_id: Any,
    endpoint: str,
    request_fingerprint: str,
) -> Optional[ReplayedResponse]:
    """Claim the key, or return the response of the attempt that already owns it.

    Returns ``None`` when the caller now owns the key and should execute the
    operation. Raises 409 if an identical request is still in flight, 422 if the
    key was reused with a different payload.
    """
    expires_at = datetime.now(timezone.utc) + timedelta(hours=settings.IDEMPOTENCY_TTL_HOURS)
    record = IdempotencyKey(
        key=key,
        user_id=user_id,
        endpoint=endpoint,
        request_fingerprint=request_fingerprint,
        status=STATUS_IN_PROGRESS,
        request_id=get_request_id(),
        expires_at=expires_at,
    )
    db.add(record)
    try:
        # Commit so the claim is visible to concurrent workers immediately, and
        # survives a rollback of the business transaction that follows.
        db.commit()
        return None
    except IntegrityError:
        db.rollback()

    existing = (
        db.query(IdempotencyKey)
        .filter(
            IdempotencyKey.user_id == user_id,
            IdempotencyKey.endpoint == endpoint,
            IdempotencyKey.key == key,
        )
        .first()
    )
    if existing is None:
        # The row vanished between the conflict and this read (TTL purge). The
        # client is free to retry cleanly.
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Idempotency key state changed concurrently; please retry",
        )

    if existing.request_fingerprint != request_fingerprint:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Idempotency-Key was already used with a different request body",
        )

    if existing.status == STATUS_COMPLETED:
        if metrics.enabled():
            metrics.idempotent_replays_total.labels(endpoint=endpoint).inc()
        logger.info(
            "replaying idempotent response",
            extra={
                "idempotency_key": key,
                "endpoint": endpoint,
                "original_request_id": existing.request_id,
                "order_id": str(existing.order_id) if existing.order_id else None,
            },
        )
        return ReplayedResponse(existing.response_status_code or 200, existing.response_body)

    # Still in flight: the first attempt has not returned yet. 409 tells the
    # client to back off rather than risk a second order.
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="A request with this Idempotency-Key is currently being processed",
        headers={"Retry-After": "2"},
    )


def complete(
    db: Session,
    *,
    key: str,
    user_id: Any,
    endpoint: str,
    status_code: int,
    body: Any,
    entity_id: Optional[Any] = None,
) -> None:
    """Store the response so future retries replay it."""
    record = (
        db.query(IdempotencyKey)
        .filter(
            IdempotencyKey.user_id == user_id,
            IdempotencyKey.endpoint == endpoint,
            IdempotencyKey.key == key,
        )
        .first()
    )
    if record is None:
        logger.warning("idempotency record missing on completion", extra={"idempotency_key": key})
        return

    record.status = STATUS_COMPLETED
    record.response_status_code = status_code
    record.response_body = body
    record.order_id = entity_id
    db.commit()


def release(db: Session, *, key: str, user_id: Any, endpoint: str) -> None:
    """Drop an unfinished reservation so a legitimate retry can proceed.

    Called when the operation failed deterministically (empty cart, bad
    address). Those are not "already applied" outcomes, so holding the key
    would only force the client to invent a new one.
    """
    try:
        db.query(IdempotencyKey).filter(
            IdempotencyKey.user_id == user_id,
            IdempotencyKey.endpoint == endpoint,
            IdempotencyKey.key == key,
            IdempotencyKey.status == STATUS_IN_PROGRESS,
        ).delete(synchronize_session=False)
        db.commit()
    except Exception as exc:  # noqa: BLE001
        logger.warning("failed to release idempotency key", extra={"error": str(exc)})
        db.rollback()


def purge_expired(db: Session) -> int:
    """Delete keys past their TTL. Intended for a scheduled maintenance job."""
    deleted = (
        db.query(IdempotencyKey)
        .filter(IdempotencyKey.expires_at < datetime.now(timezone.utc))
        .delete(synchronize_session=False)
    )
    db.commit()
    return deleted
