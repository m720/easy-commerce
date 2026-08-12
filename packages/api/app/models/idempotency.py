import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.database.base import Base


class IdempotencyKey(Base):
    """A client-supplied key that makes an unsafe POST safe to retry.

    The unique constraint on ``(user_id, endpoint, key)`` is the concurrency
    control: two simultaneous retries race to INSERT, the loser gets an
    integrity error and is told the original is still in flight. Scoping by
    user prevents one client's key from colliding with — or replaying — another
    client's order.

    See docs/adr/0003-idempotency-keys-for-checkout.md.
    """

    __tablename__ = "idempotency_keys"
    __table_args__ = (
        UniqueConstraint("user_id", "endpoint", "key", name="uq_idempotency_user_endpoint_key"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key = Column(String(255), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    endpoint = Column(String(255), nullable=False)
    # SHA-256 of the request body. A key replayed with a different payload is a
    # client bug, not a retry, and must not silently return the first response.
    request_fingerprint = Column(String(64), nullable=False)
    # "in_progress" until the handler returns; "completed" once a response is stored.
    status = Column(String(20), nullable=False, default="in_progress")
    response_status_code = Column(Integer, nullable=True)
    response_body = Column(JSONB, nullable=True)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id", ondelete="SET NULL"), nullable=True)
    request_id = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
