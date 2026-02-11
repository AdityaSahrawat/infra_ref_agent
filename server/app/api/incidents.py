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
from app.llm.model import analyze_incident_with_llm

router = APIRouter()
logger = get_logger(__name__)


@router.get("/" , response_model=List[IncidentRead])
async def get_incidents(db:Session = Depends(get_db)):

    logger.info("Fetching all incidents")
    Incidents = db.execute(select(Incident)).scalars().all()

    return Incidents 


@router.get("/{incident_id}" , response_model=IncidentRead)
async def get_incident_by_id(incident_id: UUID , db : Session = Depends(get_db)):
    logger.info(f"Fetching incident with ID: {incident_id}")

    incident = db.execute(select(Incident).where(Incident.id == incident_id)).scalar_one_or_none()

    if not incident:
        raise HTTPException(status_code=404 , detail="Incident not found")
    
    return incident
     

@router.post("/" , response_model=IncidentRead , status_code=status.HTTP_201_CREATED)
async def create_incident(payload : IncidentCreate , db : Session = Depends(get_db)):
    data = payload.model_dump()
    incident = Incident(
        alert_name=data["alert_name"],
        severity=data["severity"],
        instance=data["instance"],
        status=data["status"],
        startedAt=data["started_at"],
        receivedAt=data["received_at"],
        rawAlert=data["raw_alert"],
        matric_summary="",
    )

    db.add(incident)
    db.commit()
    db.refresh(incident)

    llm_result = analyze_incident_with_llm({
        "alert_name": incident.alert_name,
        "severity": incident.severity,
        "instance": incident.instance,
        "raw_alert": incident.rawAlert,
    })
    
    # Update incident with LLM analysis
    incident.root_cause = llm_result.get("root_cause")
    incident.recommended_action = llm_result.get("recommended_action")
    incident.llm_confidence = llm_result.get("confidence")
    
    db.commit()
    db.refresh(incident)

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


@router.patch("/{incident_id}" ,response_model=IncidentUpdate)
async def update_incident(incident_id: UUID ,payload: IncidentUpdate, db : Session = Depends(get_db)):

    incident = db.get(Incident , incident_id)
           
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    updates = payload.model_dump(exclude_unset=True)

    field_map = {
        "ended_at": "endedAt",
        "metrics_summary": "matric_summary",
    }

    for field, value in updates.items():
        target_field = field_map.get(field, field)
        setattr(incident, target_field, value)

    db.commit()
    db.refresh(incident)

    return payload

