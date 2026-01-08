# app/agents/agent.py
import asyncio
import uuid
from datetime import datetime
from app.models.alert_model import AlertModel
from app.services.logger import get_logger
from app.api.incidents import incidents_store, incidents_lock  # see incidents snippet

logger = get_logger(__name__)

async def handle_alert(alert: AlertModel):
    """
    Process the received alert (background task)
    """
    incident_id = str(uuid.uuid4())
    summary = f"status={alert.status}, labels={alert.labels}"
    logger.info(f"Alert received: {summary} (incident_id={incident_id})")

    # mark incident as 'received' in the store
    incident = {
        "id": incident_id,
        "received_at": datetime.utcnow().isoformat(),
        "alert": alert.dict(),
        "diagnosis": None,
        "recommended_action": None,
        "status": "processing"
    }

    # safe append (async lock)
    async with incidents_lock:
        incidents_store.append(incident)

    # Simulate analysis - replace later with Prometheus + LLM call
    await asyncio.sleep(0.2)
    diagnosis = "dummy: no root cause (MVP)"
    recommended_action = "notify"

    # update incident
    incident.update({
        "diagnosis": diagnosis,
        "recommended_action": recommended_action,
        "completed_at": datetime.utcnow().isoformat(),
        "status": "completed"
    })

    logger.info(f"Alert analysis completed (incident_id={incident_id}) - action: {recommended_action}")
