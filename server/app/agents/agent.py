from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping

from fastapi.encoders import jsonable_encoder

from app.database.engine import SessionLocal
from app.database.models import Action, Incident
from app.executor.executor import execute_tool
from app.llm.model import analyze_incident_with_llm, analyze_incident_followup
from app.rag.embeddings import build_query_text, get_embedding
from app.rag.retriever import retrieve_context
from app.services.logger import get_logger

logger = get_logger(__name__)

# ── Multi-turn loop configuration ──────────────────────────────────────────────
# Maximum number of diagnostic tool calls before forcing a final remediation
# decision. After MAX_DIAGNOSTIC_TURNS the agent makes one final LLM call with
# turns_remaining=0 which forces a remediation choice.
MAX_DIAGNOSTIC_TURNS = 3

# Tools that only observe the cluster — they trigger a follow-up LLM turn.
DIAGNOSTIC_TOOLS: frozenset[str] = frozenset({"get_pod_logs", "get_pod_status", "list_pods"})

# Tools that mutate the cluster — they end the loop immediately.
REMEDIATION_TOOLS: frozenset[str] = frozenset({
    "restart_deployment",
    "scale_deployment",
    "delete_pod",
    "verify_deployment_health",
})
# ───────────────────────────────────────────────────────────────────────────────


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


def _normalize_tool_args(tool_name: str, tool_args: dict, service: str) -> dict:
    """Ensure deployment/pod name fallback is set when missing from tool_args."""
    args = dict(tool_args)
    if tool_name in ("restart_deployment", "scale_deployment", "get_pod_status", "verify_deployment_health"):
        if "deployment" not in args and "deployment_name" not in args and service != "unknown":
            args["deployment"] = service
    return args


def run_agentic_loop(
    incident_data: dict,
    rag_context: dict,
    service: str,
    incident_db_obj: "Incident",
    db: Any,
) -> tuple[dict, list[dict]]:
    """
    Multi-turn agentic reasoning loop.

    Runs the LLM iteratively:
    - Turn 1 uses analyze_incident_with_llm (initial triage with RAG context).
    - Subsequent turns use analyze_incident_followup (injects tool execution history).
    - Diagnostic tools (get_pod_logs, get_pod_status, list_pods) are executed and
      their output is appended to tool_execution_history for the next turn.
    - Remediation tools (restart_deployment, scale_deployment, delete_pod) end the loop.
    - After MAX_DIAGNOSTIC_TURNS diagnostic calls, a final forced-decision call is made.

    Each diagnostic tool execution is persisted as an Action with status='diagnostic'
    so the UI can show what the agent observed during investigation.

    Returns:
        (final_llm_result, tool_execution_history)
    """
    tool_execution_history: list[dict] = []
    diagnostic_turns_used = 0
    llm_result: dict = {}

    for turn in range(1, MAX_DIAGNOSTIC_TURNS + 2):  # +2: turns 1..MAX+1 (forced decision slot)
        turns_remaining = MAX_DIAGNOSTIC_TURNS - diagnostic_turns_used

        # ── LLM Call ────────────────────────────────────────────────────────────
        if turn == 1:
            logger.info("[Agent Loop] Turn 1 — initial LLM triage")
            llm_result = analyze_incident_with_llm(incident_data, context=rag_context)
        else:
            logger.info(
                "[Agent Loop] Turn %d — follow-up LLM call (diagnostic turns used: %d, remaining: %d)",
                turn,
                diagnostic_turns_used,
                turns_remaining,
            )
            llm_result = analyze_incident_followup(
                incident=incident_data,
                context=rag_context,
                tool_execution_history=tool_execution_history,
                turn_number=turn,
                turns_remaining=turns_remaining,
            )

        tool_name: str | None = llm_result.get("tool")
        tool_args: dict = llm_result.get("args") or {}
        tool_args = _normalize_tool_args(tool_name or "", tool_args, service)

        logger.info(
            "[Agent Loop] Turn %d result — tool=%s confidence=%.2f root_cause=%r",
            turn,
            tool_name,
            llm_result.get("confidence", 0.0),
            llm_result.get("root_cause"),
        )

        # ── Forced decision reached (turns_remaining == 0 was passed to LLM) ───
        # The forced prompt told the LLM to pick a remediation tool. If it still
        # returned a diagnostic tool (LLM misbehaviour), we break and return what
        # we have — the caller will handle the low-confidence result gracefully.
        if turns_remaining == 0:
            if tool_name in DIAGNOSTIC_TOOLS:
                logger.warning(
                    "[Agent Loop] LLM returned diagnostic tool '%s' even after FORCED DECISION prompt. "
                    "Discarding tool, committing result as-is.",
                    tool_name,
                )
                llm_result = {**llm_result, "tool": None}
            break

        # ── Diagnostic tool selected — execute and loop ──────────────────────────
        if tool_name in DIAGNOSTIC_TOOLS:
            diagnostic_turns_used += 1
            logger.info(
                "[Agent Loop] Executing diagnostic tool '%s' (diagnostic turn %d/%d)",
                tool_name,
                diagnostic_turns_used,
                MAX_DIAGNOSTIC_TURNS,
            )

            exec_res = execute_tool(tool_name, tool_args)

            # Persist each diagnostic observation as an Action record (status='diagnostic')
            try:
                diag_action = Action(
                    incident_id=incident_db_obj.id,
                    action_type=tool_name,
                    action_payload={
                        "tool": tool_name,
                        "args": tool_args,
                        "result": exec_res.get("result"),
                        "logs": exec_res.get("logs", ""),
                        "executed_at": exec_res.get("executed_at"),
                        "source": "agent_diagnostic",
                        "turn": turn,
                    },
                    status="diagnostic",
                    executed_at=datetime.utcnow(),
                    error_message=exec_res.get("error"),
                )
                db.add(diag_action)
                db.commit()
                logger.info(
                    "[Agent Loop] Saved diagnostic Action for turn %d, tool='%s'",
                    turn,
                    tool_name,
                )
            except Exception:
                logger.exception("[Agent Loop] Failed to persist diagnostic Action for turn %d", turn)
                db.rollback()

            # Append execution result to history for the next LLM turn
            tool_execution_history.append({
                "turn": turn,
                "tool": tool_name,
                "args": tool_args,
                "success": exec_res.get("success"),
                "result": exec_res.get("result"),
                "logs": exec_res.get("logs", ""),
                "error": exec_res.get("error"),
            })

            # After using all diagnostic turns, the next iteration will be the
            # forced-decision call (turns_remaining will be 0).
            continue

        # ── Remediation tool (or null) — exit loop ───────────────────────────────
        break

    return llm_result, tool_execution_history


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

            # ── Step 1: RAG — embed alert and retrieve historical context ─────────
            query_embedding = None
            rag_context = {
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
                rag_context = retrieve_context(
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

            # ── Step 2: Multi-turn agentic reasoning loop ─────────────────────────
            incident_data = {
                "alert_name": alert_name,
                "severity": severity,
                "instance": instance,
                "service": service,
                "metrics_summary": metrics_summary,
                "raw_alert": data,
            }

            llm_result, tool_execution_history = run_agentic_loop(
                incident_data=incident_data,
                rag_context=rag_context,
                service=service,
                incident_db_obj=incident,
                db=db,
            )

            tool_name = llm_result.get("tool")
            tool_args = llm_result.get("args") or {}

            # Fallback tool inference if LLM produced no explicit tool name
            if not tool_name and llm_result.get("recommended_action"):
                action_text = (llm_result.get("recommended_action") or "").lower()
                if "scale" in action_text:
                    tool_name = "scale_deployment"
                    tool_args = {"deployment": service if service != "unknown" else "auth-api", "replicas": 3}
                elif "restart" in action_text:
                    tool_name = "restart_deployment"
                    tool_args = {"deployment": service if service != "unknown" else "auth-api"}

            tool_args = _normalize_tool_args(tool_name or "", tool_args, service)

            # ── Step 3: Persist LLM findings on the incident row ──────────────────
            incident.root_cause = llm_result.get("root_cause")
            incident.recommended_action = llm_result.get("recommended_action") or tool_name
            incident.llm_confidence = llm_result.get("confidence")
            incident.embedding = query_embedding
            db.commit()
            db.refresh(incident)

            logger.info(
                "Incident %s — loop complete: tool=%s confidence=%.2f diagnostic_turns=%d",
                incident.id,
                tool_name,
                incident.llm_confidence or 0.0,
                len(tool_execution_history),
            )

            # ── Step 4: Remediation decision ──────────────────────────────────────
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
                    "diagnostic_turns": len(tool_execution_history),
                }

                # Auto-execute if confidence >= 0.85
                if tool_name and incident.llm_confidence >= 0.85:
                    logger.info(
                        "High confidence (%.2f). Auto-executing remediation tool '%s'",
                        incident.llm_confidence,
                        tool_name,
                    )
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
                    # Medium confidence — queue for human approval
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
