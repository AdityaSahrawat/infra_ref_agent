from datetime import datetime, timezone
from typing import Annotated, Any
from uuid import UUID

from pydantic import BaseModel, Field, field_serializer

from app.database.schema.action import ActionRead


Embedding = Annotated[list[float], Field(min_length=768, max_length=768)]


class IncidentCreate(BaseModel):
    alert_name: str
    severity: str
    instance: str
    service: str = Field(min_length=1)
    status: str

    started_at: datetime
    received_at: datetime

    raw_alert: dict[str, Any]
    embedding: Embedding | None = None

    # Optional: allow clients to pass a precomputed summary; otherwise server fills default.
    metrics_summary: str | None = None


class IncidentUpdate(BaseModel):
    service: str | None = Field(default=None, min_length=1)
    status: str | None = None
    ended_at: datetime | None = None

    root_cause: str | None = None
    llm_confidence: float | None = None
    recommended_action: str | None = None

    metrics_summary: str | None = None
    embedding: Embedding | None = None


class IncidentRead(BaseModel):
    id: UUID

    alert_name: str
    severity: str
    instance: str
    service: str
    status: str

    started_at: datetime
    ended_at: datetime | None
    received_at: datetime
    created_at: datetime
    metrics_summary: str = Field(default="")

    root_cause: str | None
    llm_confidence: float | None
    recommended_action: str | None
    embedding: Embedding | None = None

    actions: list["ActionRead"] = Field(default_factory=list)

    @field_serializer("started_at", "ended_at", "received_at", "created_at")
    def serialize_datetime(self, v: datetime | None) -> str | None:
        if v is None:
            return None
        if v.tzinfo is None:
            v = v.replace(tzinfo=timezone.utc)
        return v.isoformat().replace("+00:00", "Z")

    model_config = {
        "from_attributes": True,
    }

