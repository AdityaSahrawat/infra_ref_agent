# app/api/alerts.py
from fastapi import APIRouter, BackgroundTasks, HTTPException
from app.models.alert_model import AlertModel
from app.services.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)

@router.post("/alerts", status_code=200)
async def receive_alert(alert: AlertModel, background_tasks: BackgroundTasks):
    """
    Receive AlertManager alerts and process them in the background
    """
    try:
        logger.info(f"Received alert: {alert.dict()}")
        from app.agents.agent import handle_alert  # local import ok
        background_tasks.add_task(handle_alert, alert)
        return {"status": "received"}
    except Exception as e:
        logger.exception("Failed to enqueue alert")
        raise HTTPException(status_code=500, detail="Internal server error")
