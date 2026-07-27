from typing import Optional , List
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.database.session import get_db
from fastapi import APIRouter , HTTPException , Depends
from app.database.schema import ActionCreate , ActionRead , ActionUpdate
from app.database.models import Action , Incident
from app.executor.executor import execute_action_payload, execute_tool
from app.services.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.post("/{incident_id}/actions" , response_model=ActionRead)
async def create_action(incident_id: UUID, payload: ActionCreate, db: Session = Depends(get_db)):

    incident = db.get(Incident , incident_id)

    if not incident:
        raise HTTPException(status_code=404 , detail=f"Incident not found for id : {incident_id}")
    

    action = Action(
        incident_id=incident_id,
        **payload.model_dump(),
    )

    db.add(action)
    db.commit()
    db.refresh(action)

    return action


@router.get("/actions" , response_model=List[ActionRead])
async def get_action(incident_id : Optional[UUID] = None, db : Session = Depends(get_db)):

    stmt = select(Action)

    if incident_id:
        stmt = stmt.where(Action.incident_id == incident_id)

    actions = db.execute(stmt).scalars().all()

    return actions


@router.get("/actions/{action_id}" , response_model=ActionRead)
async def get_action_by_id(action_id: UUID, db : Session = Depends(get_db)):


    action = db.get(Action, action_id)

    if not action:
        raise HTTPException(status_code=404 , detail=f"No Action found for id : {action_id}")

    return action

@router.patch("/actions/{action_id}" , response_model=ActionRead)
def execute_action(
    action_id: UUID,
    db: Session = Depends(get_db),
):
    # 1 Fetch action
    action = db.get(Action, action_id)
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")

    # 2 Execute tool against Kubernetes
    payload = dict(action.action_payload or {})
    tool_name = payload.get("tool") or action.action_type
    tool_args = payload.get("args") or {}

    # Tool fallback inference if action_type contains verb
    if not tool_name or tool_name not in ("restart_deployment", "scale_deployment", "delete_pod", "get_pod_logs", "list_pods", "get_pod_status", "verify_deployment_health"):
        if "scale" in action.action_type.lower():
            tool_name = "scale_deployment"
            if "replicas" not in tool_args:
                tool_args["replicas"] = 3
        elif "restart" in action.action_type.lower():
            tool_name = "restart_deployment"

    if "deployment" not in tool_args and "deployment_name" not in tool_args:
        incident = db.get(Incident, action.incident_id)
        if incident and incident.service and incident.service != "unknown":
            tool_args["deployment"] = incident.service

    exec_res = execute_tool(tool_name=tool_name, args=tool_args)

    # 3 Update Action record
    action.status = "executed" if exec_res.get("success") else "failed"
    action.executed_at = datetime.utcnow()
    action.error_message = exec_res.get("error")

    # Preserve execution results in payload
    updated_payload = dict(action.action_payload or {})
    updated_payload["tool"] = tool_name
    updated_payload["args"] = tool_args
    updated_payload["result"] = exec_res.get("result")
    updated_payload["logs"] = exec_res.get("logs", "")
    updated_payload["executed_at"] = exec_res.get("executed_at")
    action.action_payload = updated_payload

    db.commit()
    db.refresh(action)

    # 4 RESOLVE INCIDENT IF EXECUTED SUCCESSFULLY
    if exec_res.get("success"):
        incident = db.get(Incident, action.incident_id)
        if incident and incident.status != "resolved":
            incident.status = "resolved"
            incident.ended_at = datetime.utcnow()
            db.commit()

    return action
