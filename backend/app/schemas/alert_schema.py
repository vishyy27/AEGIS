from pydantic import BaseModel
from datetime import datetime


class AlertResponse(BaseModel):
    alert_id: int
    deployment_id: int
    risk_score: float
    id: int
    deployment_id: int
    alert_type: str
    severity: str
    message: str
    timestamp: datetime
