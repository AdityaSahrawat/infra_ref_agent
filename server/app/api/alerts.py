# app/api/alerts.py
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field

from app.services.logger import get_logger


class AlertModel(BaseModel):
    """Represents a single alert (matches Alertmanager's per-alert shape)."""

    status: str
    labels: Dict[str, Any] = Field(default_factory=dict)
    annotations: Dict[str, Any] = Field(default_factory=dict)
    startsAt: Optional[datetime] = None
    endsAt: Optional[datetime] = None
    generatorURL: Optional[str] = None

    model_config = {"extra": "allow"}


class AlertmanagerWebhook(BaseModel):
    """Represents an Alertmanager webhook payload (contains a list of alerts)."""

    status: str
    alerts: List[AlertModel] = Field(default_factory=list)

    model_config = {"extra": "allow"}


AlertPayload = Union[AlertModel, AlertmanagerWebhook]

router = APIRouter()
logger = get_logger(__name__)

@router.post("/", status_code=200)
@router.post("/alerts", status_code=200, include_in_schema=False)
async def receive_alert(payload: AlertPayload, background_tasks: BackgroundTasks):
    """
    Receive Alertmanager alerts and process them in the background.

    Supports both:
    - a single alert object
    - the full Alertmanager webhook payload with an `alerts` list
    """
    try:
        logger.info("Received alert payload")
        from app.agents.agent import handle_alert  # local import ok

        alerts: List[AlertModel]
        if isinstance(payload, AlertmanagerWebhook):
            alerts = payload.alerts
        else:
            alerts = [payload]

        for alert in alerts:
            background_tasks.add_task(handle_alert, alert)
        return {"status": "received"}
    except Exception:
        logger.exception("Failed to enqueue alert")
        raise HTTPException(status_code=500, detail="Internal server error")
