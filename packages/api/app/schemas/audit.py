from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class AuditLogResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    actor_user_id: Optional[UUID] = None
    actor_email: Optional[str] = None
    action: str
    entity_type: str
    entity_id: Optional[str] = None
    entity_label: Optional[str] = None
    changes: Optional[dict] = None
    request_id: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: datetime
