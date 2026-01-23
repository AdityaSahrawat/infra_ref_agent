# app/api/incidents.py
from typing import List
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.services.logger import get_logger
from app.database.session import get_db
from sqlalchemy import select
from app.database.models import Incident
from app.database.schema import IncidentRead
router = APIRouter()
logger = get_logger(__name__)


@router.get("/incidents" , response_model=List[IncidentRead])
async def get_incidents(db:Session = Depends(get_db())):

    logger.info("Fetching all incidents")
    Incidents = db.execute(select(Incident)).scalars().all()

    return Incidents

@router.get("/incidents/{incident_id}")
async def get_incident(incident_id: str):
    logger.info(f"Fetching incident with ID: {incident_id}")
     

@router.post("/incident")
async def create_incident(plyload : create_incident):
    return []
