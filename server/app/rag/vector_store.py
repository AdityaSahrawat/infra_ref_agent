from sqlalchemy import select
from sqlalchemy.orm import Session
from uuid import UUID

from app.database.models import Incident


def search_similar_incidents(
    db: Session,
    embedding: list[float],
    limit: int = 5,
    exclude_incident_id: UUID | None = None,
):
    stmt = select(Incident).where(Incident.embedding.isnot(None))

    if exclude_incident_id is not None:
        stmt = stmt.where(Incident.id != exclude_incident_id)

    stmt = (
        stmt.order_by(Incident.embedding.cosine_distance(embedding))
        .limit(limit)
    )

    return list(db.scalars(stmt))
