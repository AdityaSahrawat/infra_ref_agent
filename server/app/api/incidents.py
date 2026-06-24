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
from app.rag.embeddings import (
    build_query_text,
    get_embedding,
)
from app.rag.retriever import retrieve_context

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
        service=data["service"],
        status=data["status"],
        started_at=data["started_at"],
        received_at=data["received_at"],
        raw_alert=data["raw_alert"],
        metrics_summary=data.get("metrics_summary") or "",
        embedding=data.get("embedding"),
    )

    db.add(incident)
    db.commit()
    db.refresh(incident)

    query_embedding = None
    context = {
        "similar_incidents": [],
        "service_history": [],
        "alert_history": [],
    }
    try:
        query_text = build_query_text(
            payload.alert_name,
            payload.service,
            payload.severity,
            payload.metrics_summary,
        )

        query_embedding = get_embedding(query_text)
        context = retrieve_context(
            db=db,
            query_embedding=query_embedding,
            service=payload.service,
            alert_name=payload.alert_name,
            exclude_incident_id=incident.id,
        )
    except Exception:
        logger.exception(
            "Embedding/RAG retrieval failed; continuing without historical context"
        )


    llm_result = analyze_incident_with_llm(
        {
            "alert_name": incident.alert_name,
            "severity": incident.severity,
            "instance": incident.instance,
            "service": incident.service,
            "metrics_summary": incident.metrics_summary,
            "raw_alert": incident.raw_alert,
        },
        context=context,
    )

    # Update incident with LLM analysis
    incident.root_cause = llm_result.get("root_cause")
    incident.recommended_action = llm_result.get("recommended_action")
    incident.llm_confidence = llm_result.get("confidence")
    incident.embedding = query_embedding

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


@router.patch("/{incident_id}" ,response_model=IncidentRead)
async def update_incident(incident_id: UUID ,payload: IncidentUpdate, db : Session = Depends(get_db)):

    incident = db.get(Incident , incident_id)

    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    updates = payload.model_dump(exclude_unset=True)

    for field, value in updates.items():
        setattr(incident, field, value)

    db.commit()
    db.refresh(incident)

    return incident

