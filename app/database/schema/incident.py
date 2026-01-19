from typing import Dict , List ,Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from uuid import UUID
from app.database.schema.action import ActionRead

class IncidentCreate(BaseModel):
    alert_name: str
    severity: str
    instance: str
    status: str

    started_at: datetime
    received_at: datetime

    raw_alert: Dict[str, Any]


class IncidentUpdate(BaseModel):
    status: Optional[str] = None
    ended_at: Optional[datetime] = None

    root_cause: Optional[str] = None
    llm_confidence: Optional[float] = None
    recommended_action: Optional[str] = None

    metrics_summary: Optional[Dict[str, Any]] = None


class IncidentRead(BaseModel):
    id: UUID

    alert_name: str
    severity: str
    instance: str
    status: str

    started_at: datetime
    ended_at: Optional[datetime]
    received_at: datetime
    created_at: datetime

    root_cause: Optional[str]
    llm_confidence: Optional[float]
    recommended_action: Optional[str]

    actions: List["ActionRead"] = Field(default_factory=list)

    model_config = {
        "from_attributes": True
    }