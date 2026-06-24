from sqlalchemy import select
from sqlalchemy.orm import Session
from uuid import UUID

from app.database.models import Incident

from app.rag.vector_store import (
    search_similar_incidents,
)


def get_service_history(
    db: Session,
    service: str,
    limit: int = 10,
    exclude_incident_id: UUID | None = None,
):
    stmt = select(Incident).where(Incident.service == service)

    if exclude_incident_id is not None:
        stmt = stmt.where(Incident.id != exclude_incident_id)

    stmt = stmt.order_by(Incident.received_at.desc()).limit(limit)

    return list(db.scalars(stmt))


def get_alert_history(
    db: Session,
    alert_name: str,
    limit: int = 10,
    exclude_incident_id: UUID | None = None,
):
    stmt = select(Incident).where(Incident.alert_name == alert_name)

    if exclude_incident_id is not None:
        stmt = stmt.where(Incident.id != exclude_incident_id)

    stmt = stmt.order_by(Incident.received_at.desc()).limit(limit)

    return list(db.scalars(stmt))


def retrieve_context(
    db: Session,
    query_embedding: list[float],
    service: str | None,
    alert_name: str,
    exclude_incident_id: UUID | None = None,
):
    similar_incidents = search_similar_incidents(
        db,
        query_embedding,
        limit=5,
        exclude_incident_id=exclude_incident_id,
    )

    service_history = []

    if service:
        service_history = get_service_history(
            db,
            service,
            limit=10,
            exclude_incident_id=exclude_incident_id,
        )

    alert_history = get_alert_history(
        db,
        alert_name,
        limit=10,
        exclude_incident_id=exclude_incident_id,
    )

    return {
        "similar_incidents": [_serialize_incident(item) for item in similar_incidents],
        "service_history": [_serialize_incident(item) for item in service_history],
        "alert_history": [_serialize_incident(item) for item in alert_history],
    }


def _serialize_incident(incident: Incident) -> dict:
    """Return only the historical fields that are useful to the LLM prompt."""

    return {
        "id": str(incident.id),
        "alert_name": incident.alert_name,
        "service": incident.service,
        "severity": incident.severity,
        "status": incident.status,
        "metrics_summary": incident.metrics_summary,
        "root_cause": incident.root_cause,
        "recommended_action": incident.recommended_action,
        "llm_confidence": incident.llm_confidence,
        "received_at": incident.received_at.isoformat(),
    }
