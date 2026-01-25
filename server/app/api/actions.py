from typing import Optional , List
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.database.session import get_db
from fastapi import APIRouter , HTTPException , Depends
from app.database.schema import ActionCreate , ActionRead , ActionUpdate
from app.database.models import Action , Incident
from app.services.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.post("/action" , response_model=ActionCreate)
async def create_action(payload : ActionCreate , incident_id : UUID, db: Session = Depends(get_db)):

    incident = db.get(Incident , incident_id)

    if not incident:
        raise HTTPException(status_code=404 , detail=f"Incident not found for id : {incident_id}")
    

    action = Action(incident_id = incident_id , **payload.model_dump())

    db.add(action)
    db.commit()
    db.refresh(action)

    return action


@router.get("/action" , response_model=List[ActionRead])
async def get_action(incident_id : Optional[str] = None, db : Session = Depends(get_db)):

    stmt = select(Action)

    if incident_id:
        stmt = stmt.where(incident_id == incident_id)

    actions = db.execute(stmt).scalars().all()

    return actions


@router.get("/action/{action_id}" , response_model=Action)
async def get_action_by_id(action_id : str , db : Session = Depends(get_db)):


    action = db.get(Action , action_id)

    if not action:
        raise HTTPException(status_code=404 , detail=f"No Action found for id : {action_id}")

    return action

