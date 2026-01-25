from typing import Dict , List ,Any, Optional
from datetime import datetime
from pydantic import BaseModel
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

    model_config = {
        "from_attributes": True
    }
