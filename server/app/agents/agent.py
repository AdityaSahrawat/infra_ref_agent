from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping

from app.database.engine import SessionLocal
from app.database.models import Action, Incident
from app.llm.model import analyze_incident_with_llm
from app.services.logger import get_logger

logger = get_logger(__name__)


def _coerce_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        dt = value
    elif isinstance(value, str):
        raw = value.strip()
        # Handle RFC3339 "Z" suffix.
        if raw.endswith("Z"):
            raw = raw[:-1] + "+00:00"
        try:
            dt = datetime.fromisoformat(raw)
        except ValueError:
            return datetime.utcnow()
    else:
        return datetime.utcnow()

    # Normalize to naive UTC (matches how the rest of the app uses timestamps).
    if dt.tzinfo is None:
        return dt
    return dt.astimezone(timezone.utc).replace(tzinfo=None)


def _stringify(value: Any, default: str = "") -> str:
    if value is None:
        return default
    try:
        text = str(value)
    except Exception:
        return default
    return text if text else default


def handle_alert(alert: Any) -> None:
    """Background task entrypoint.

    This function must never raise (it's executed as a background task).
    """

    try:
        data: Mapping[str, Any]
        if hasattr(alert, "model_dump"):
            data = alert.model_dump()  # type: ignore[assignment]
        elif isinstance(alert, Mapping):
            data = alert
        else:
            logger.warning("Unsupported alert payload type: %s", type(alert))
            return

        labels = data.get("labels") or {}
        annotations = data.get("annotations") or {}

        alert_name = _stringify(labels.get("alertname") or labels.get("alert_name"), default="unknown")
        severity = _stringify(labels.get("severity"), default="unknown")
        instance = _stringify(
            labels.get("instance")
            or labels.get("pod")
            or labels.get("node")
            or labels.get("host"),
            default="unknown",
        )
        status = _stringify(data.get("status"), default="firing")

        started_at = _coerce_datetime(data.get("startsAt") or data.get("startedAt") or data.get("starts_at"))

        ended_at = None
        if status == "resolved":
            ended_at = _coerce_datetime(data.get("endsAt") or data.get("endedAt") or data.get("ends_at"))

        metrics_summary = _stringify(
            annotations.get("summary") or annotations.get("description") or annotations.get("message"),
            default="",
        )

        llm_result = analyze_incident_with_llm(
            {
                "alert_name": alert_name,
                "severity": severity,
                "instance": instance,
                "raw_alert": dict(data),
            }
        )

        db = SessionLocal()
        try:
            incident = Incident(
                alert_name=alert_name,
                severity=severity,
                instance=instance,
                status=status,
                started_at=started_at,
                ended_at=ended_at,
                received_at=datetime.utcnow(),
                raw_alert=dict(data),
                metrics_summary=metrics_summary,
                root_cause=llm_result.get("root_cause"),
                recommended_action=llm_result.get("recommended_action"),
                llm_confidence=llm_result.get("confidence"),
            )

            db.add(incident)
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

            logger.info("Incident created from alert: %s (%s)", incident.id, alert_name)
        finally:
            db.close()

    except Exception:
        logger.exception("handle_alert failed")
