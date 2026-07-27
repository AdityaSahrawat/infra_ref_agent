from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping

from fastapi.encoders import jsonable_encoder

from app.database.engine import SessionLocal
from app.database.models import Action, Incident
from app.executor.executor import execute_tool
from app.llm.model import analyze_incident_with_llm
from app.rag.embeddings import build_query_text, get_embedding
from app.rag.retriever import retrieve_context
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

        # Pydantic's default model_dump() keeps datetime objects in Python mode.
        # Encode the complete nested payload before storing it in a JSON column.
        encoded_data = jsonable_encoder(dict(data))
        if not isinstance(encoded_data, dict):
            logger.warning("Alert payload did not encode to a JSON object")
            return
        data = encoded_data

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
        service = _stringify(
            labels.get("service")
            or labels.get("app")
            or labels.get("job"),
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

        db = SessionLocal()
        try:
            incident = Incident(
                alert_name=alert_name,
                severity=severity,
                instance=instance,
                service=service,
                status=status,
                started_at=started_at,
                ended_at=ended_at,
                received_at=datetime.utcnow(),
                raw_alert=data,
                metrics_summary=metrics_summary,
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
                    alert_name=alert_name,
                    service=service,
                    severity=severity,
                    metrics_summary=metrics_summary,
                )
                query_embedding = get_embedding(query_text)
                context = retrieve_context(
                    db=db,
                    query_embedding=query_embedding,
                    service=service,
                    alert_name=alert_name,
                    exclude_incident_id=incident.id,
                )
            except Exception:
                logger.exception(
                    "Embedding/RAG retrieval failed; continuing without historical context"
                )

            llm_result = analyze_incident_with_llm(
                {
                    "alert_name": alert_name,
                    "severity": severity,
                    "instance": instance,
                    "service": service,
                    "metrics_summary": metrics_summary,
                    "raw_alert": data,
                },
                context=context,
            )

            tool_name = llm_result.get("tool")
            tool_args = llm_result.get("args") or {}

            # Fallback tool inference if not explicitly output by LLM
            if not tool_name and incident.recommended_action:
                action_text = incident.recommended_action.lower()
                if "scale" in action_text:
                    tool_name = "scale_deployment"
                    tool_args = {"deployment": service if service != "unknown" else "auth-api", "replicas": 3}
                elif "restart" in action_text:
                    tool_name = "restart_deployment"
                    tool_args = {"deployment": service if service != "unknown" else "auth-api"}

            # Ensure deployment name fallback if missing in tool_args
            if tool_name in ("restart_deployment", "scale_deployment", "get_pod_status", "verify_deployment_health"):
                if "deployment" not in tool_args and "deployment_name" not in tool_args and service != "unknown":
                    tool_args["deployment"] = service

            incident.root_cause = llm_result.get("root_cause")
            incident.recommended_action = llm_result.get("recommended_action") or tool_name
            incident.llm_confidence = llm_result.get("confidence")
            incident.embedding = query_embedding
            db.commit()
            db.refresh(incident)

            if (
                incident.severity == "critical"
                and incident.llm_confidence is not None
                and incident.llm_confidence >= 0.7
                and (tool_name or incident.recommended_action)
            ):
                action_type_str = tool_name or incident.recommended_action
                payload_data = {
                    "tool": tool_name or incident.recommended_action,
                    "args": tool_args,
                    "source": "llm",
                    "confidence": incident.llm_confidence,
                }

                # Auto-execute if confidence >= 0.85
                if tool_name and incident.llm_confidence >= 0.85:
                    logger.info("High confidence (%.2f). Auto-executing tool '%s'", incident.llm_confidence, tool_name)
                    exec_res = execute_tool(tool_name, tool_args)
                    
                    status_str = "executed" if exec_res.get("success") else "failed"
                    payload_data["result"] = exec_res.get("result")
                    payload_data["logs"] = exec_res.get("logs", "")
                    payload_data["executed_at"] = exec_res.get("executed_at")

                    action = Action(
                        incident_id=incident.id,
                        action_type=action_type_str,
                        action_payload=payload_data,
                        status=status_str,
                        executed_at=datetime.utcnow(),
                        error_message=exec_res.get("error"),
                    )
                    db.add(action)
                    
                    if exec_res.get("success"):
                        incident.status = "resolved"
                        incident.ended_at = datetime.utcnow()
                    
                    db.commit()
                else:
                    # Require human approval for medium-confidence actions
                    action = Action(
                        incident_id=incident.id,
                        action_type=action_type_str,
                        action_payload=payload_data,
                        status="pending",
                    )
                    db.add(action)
                    db.commit()

            logger.info("Incident created from alert: %s (%s)", incident.id, alert_name)
        finally:
            db.close()

    except Exception:
        logger.exception("handle_alert failed")
