import uuid
from sqlalchemy import Float , Text, TIMESTAMP , ForeignKey
from sqlalchemy.orm import Mapped , mapped_column , relationship
from sqlalchemy.dialects.postgresql import JSONB , UUID
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
    
    startedAt : Mapped[datetime] = mapped_column(TIMESTAMP , nullable=False)
    endedAt : Mapped[datetime | None ] = mapped_column(TIMESTAMP , nullable=True)
    receivedAt : Mapped[datetime] = mapped_column(TIMESTAMP , nullable=False , default=datetime.now())

    rawAlert : Mapped[dict] = mapped_column(JSONB , nullable=False)
    matric_summary : Mapped[str] = mapped_column(Text , nullable=False)

    root_cause : Mapped[str] = mapped_column(Text , nullable=True)
    llm_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    recommended_action: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        nullable=False,
        default=datetime.now(),
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
    action_payload: Mapped[dict] = mapped_column(JSONB, nullable=False)

    status: Mapped[str] = mapped_column(Text, nullable=False)
    executed_at: Mapped[datetime | None] = mapped_column(TIMESTAMP, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    incident: Mapped["Incident"] = relationship(
        back_populates="actions"
    )