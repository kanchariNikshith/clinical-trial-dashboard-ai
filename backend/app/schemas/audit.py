"""Audit event schemas."""

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, ConfigDict


class AuditEventResponse(BaseModel):
    id: str
    actor_user_id: Optional[str] = None
    action: str
    entity_type: str
    entity_id: Optional[str] = None
    outcome: str
    occurred_at: datetime
    metadata_json: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)
