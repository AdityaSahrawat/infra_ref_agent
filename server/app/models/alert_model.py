# app/models/alert_model.py
from pydantic import BaseModel, Extra
from typing import Optional, Dict, Any
from datetime import datetime

class AlertModel(BaseModel):
    status: str
    labels: Dict[str, Any]
    annotations: Dict[str, Any]
    startsAt: Optional[datetime] = None
    endsAt: Optional[datetime] = None

    class Config:
        extra = Extra.allow  # allow other fields but ignore validation for them
