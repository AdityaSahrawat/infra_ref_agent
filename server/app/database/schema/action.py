from typing import Dict , List ,Any, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, field_serializer
from uuid import UUID


class ActionCreate(BaseModel):
    action_type: str
    action_payload: Dict[str, Any]


class ActionUpdate(BaseModel):
    status: str
    executed_at: Optional[datetime] = None
    error_message: Optional[str] = None

class ActionRead(BaseModel):
    id: UUID
    action_type: str
    action_payload: Dict[str, Any]

    status: str
    executed_at: Optional[datetime]
    error_message: Optional[str]

    @field_serializer("executed_at")
    def serialize_datetime(self, v: datetime | None) -> str | None:
        if v is None:
            return None
        if v.tzinfo is None:
            v = v.replace(tzinfo=timezone.utc)
        return v.isoformat().replace("+00:00", "Z")

    model_config = {
        "from_attributes": True
    }
