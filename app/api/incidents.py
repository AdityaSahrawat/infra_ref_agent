# app/api/incidents.py
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
import asyncio
from app.services.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)

# Shared in-memory storage + lock for thread-safety
incidents_store: List[Dict[str, Any]] = []
incidents_lock = asyncio.Lock()

@router.get("/incidents")
async def get_incidents():
    logger.info(f"Fetching all incidents, count: {len(incidents_store)}")
    return incidents_store

@router.get("/incidents/{incident_id}")
async def get_incident(incident_id: str):
    logger.info(f"Fetching incident with ID: {incident_id}")
    for incident in incidents_store:
        if incident.get("id") == incident_id:
            return incident
    logger.warning(f"Incident not found: {incident_id}")
    raise HTTPException(status_code=404, detail="Incident not found")
