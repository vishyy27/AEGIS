from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime


class AlertResponse(BaseModel):
    id: int
    deployment_id: int
    alert_type: str
    severity: str
    message: str
    incident_pattern: Optional[List[Dict]] = None
    affected_service: Optional[str] = None
    status: str = "active"
    timestamp: datetime

    class Config:
        from_attributes = True


class IncidentPatternResponse(BaseModel):
    incident_pattern: str
    severity: str
    count: int
    last_occurrence: datetime


class IncidentSummaryResponse(BaseModel):
    incidents: List[IncidentPatternResponse]
    total_incidents: int
