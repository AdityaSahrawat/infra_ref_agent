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

    started_at: datetime = Field(alias="startedAt")
    received_at: datetime = Field(alias="receivedAt")

    raw_alert: Dict[str, Any] = Field(alias="rawAlert")
    
    model_config = {
        "populate_by_name": True
    }


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

    started_at: datetime = Field(alias="startedAt")
    ended_at: Optional[datetime] = Field(default=None, alias="endedAt")
    received_at: datetime = Field(alias="receivedAt")
    created_at: datetime

    root_cause: Optional[str]
    llm_confidence: Optional[float]
    recommended_action: Optional[str]

    actions: List["ActionRead"] = Field(default_factory=list)

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }