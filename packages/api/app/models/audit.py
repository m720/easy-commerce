import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Index, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.database.base import Base


class AuditLog(Base):
    """Append-only record of privileged actions: who changed what, and to what.

    Deliberately denormalised. ``actor_email`` and ``entity_label`` are copied
    in rather than joined at read time, because the answer to "who approved
    this refund in March" must survive the actor being deleted and the entity
    being renamed. The same reasoning as the order's address snapshot.

    ``request_id`` ties each entry back to the structured request log, so an
    audit finding can be expanded into the full request trace.
    """

    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("ix_audit_logs_entity", "entity_type", "entity_id"),
        Index("ix_audit_logs_created_at", "created_at"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # SET NULL, not CASCADE: deleting an admin must not erase their trail.
    actor_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    actor_email = Column(String(255), nullable=True)
    action = Column(String(100), nullable=False, index=True)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(String(64), nullable=True)
    entity_label = Column(String(255), nullable=True)
    # Only the fields that actually changed, as {"field": {"before": x, "after": y}}.
    changes = Column(JSONB, nullable=True)
    request_id = Column(String(64), nullable=True)
    ip_address = Column(String(45), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
