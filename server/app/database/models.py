import uuid
from sqlalchemy import Float, Text, TIMESTAMP, ForeignKey, JSON, text
from sqlalchemy.orm import Mapped , mapped_column , relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from app.database.base import Base

class Incident(Base):
    __tablename__ = "incident"

    id : Mapped[uuid.UUID]= mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    alert_name : Mapped[str] = mapped_column(Text , nullable=False)
    severity : Mapped[str] = mapped_column(Text , nullable=False) 
    instance : Mapped[str] = mapped_column(Text , nullable= False)
    status : Mapped[str] = mapped_column(Text , nullable=False)
    
    started_at: Mapped[datetime] = mapped_column("startedAt", TIMESTAMP, nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column("endedAt", TIMESTAMP, nullable=True)
    received_at: Mapped[datetime] = mapped_column(
        "receivedAt",
        TIMESTAMP,
        nullable=False,
        default=datetime.utcnow,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    raw_alert: Mapped[dict] = mapped_column("rawAlert", JSON, nullable=False)
    # DB column is named 'matric_summary' (typo) - keep it, but expose a clearer Python attribute.
    metrics_summary: Mapped[str] = mapped_column(
        "matric_summary",
        Text,
        nullable=False,
        default="",
        server_default="",
    )

    root_cause : Mapped[str] = mapped_column(Text , nullable=True)
    llm_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    recommended_action: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        nullable=False,
        default=datetime.utcnow,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    actions : Mapped[list["Action"]] = relationship(
        back_populates="incident",
        cascade= "all , delete-orphan"
    )


class Action(Base):
    __tablename__ = "actions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    incident_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("incident.id", ondelete="CASCADE"),
        nullable=False,
    )

    action_type: Mapped[str] = mapped_column(Text, nullable=False)
    action_payload: Mapped[dict] = mapped_column(JSON, nullable=False)

    status: Mapped[str] = mapped_column(Text, nullable=False, default="pending", server_default="pending")
    executed_at: Mapped[datetime | None] = mapped_column(TIMESTAMP, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    incident: Mapped["Incident"] = relationship(
        back_populates="actions"
    )