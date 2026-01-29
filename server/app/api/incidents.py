# app/api/incidents.py
from typing import List
from fastapi import APIRouter, HTTPException, Depends , status
from sqlalchemy.orm import Session
from app.services.logger import get_logger
from app.database.session import get_db
from sqlalchemy import select
from app.database.models import Incident , Action
from app.database.schema import IncidentRead , IncidentCreate , IncidentUpdate
from uuid import UUID
router = APIRouter()
logger = get_logger(__name__)


@router.get("/incident" , response_model=List[IncidentRead])
async def get_incidents(db:Session = Depends(get_db)):

    logger.info("Fetching all incidents")
    Incidents = db.execute(select(Incident)).scalars().all()

    return Incidents


@router.get("/incident/{incident_id}" , response_model=IncidentRead)
async def get_incident_by_id(incident_id: str , db : Session = Depends(get_db)):
    logger.info(f"Fetching incident with ID: {incident_id}")

    incident = db.execute(select(Incident).where(Incident.id == incident_id)).scalar_one_or_none()

    if not incident:
        raise HTTPException(status_code=404 , detail="Incident not found")
    
    return incident
     

@router.post("/incident" , response_model=IncidentCreate , status_code=status.HTTP_201_CREATED)
async def create_incident(payload : IncidentCreate , db : Session = Depends(get_db)):
    incident = Incident(**payload.model_dump())

    db.add(incident)
    db.commit()
    db.refresh(incident)

    llm_result = analyze_incident_with_llm({
        "alert_name": incident.alert_name,
        "severity": incident.severity,
        "instance": incident.instance,
        "raw_alert": incident.raw_alert,
    })

    if (
        incident.severity == "critical"
        and incident.llm_confidence is not None
        and incident.llm_confidence >= 0.7
        and incident.recommended_action
        ):
        action = Action(
            incident_id=incident.id,
            action_type=incident.recommended_action,
            action_payload={"source": "llm"},
            status="pending",
        )
        db.add(action)
        db.commit()


    return incident


@router.patch("/incident/{incident_id}" ,response_model=IncidentUpdate)
async def update_incident(incident_id: str ,payload: IncidentUpdate, db : Session = Depends(get_db)):

    incident = db.get(Incident , incident_id)
           
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    updates = payload.model_dump(exclude_unset=True)

    for field, value in updates.items():
        setattr(incident, field, value)

    db.commit()
    db.refresh(incident)

    return 

