from pydantic import BaseModel
from typing import List, Optional


class IntegrationBase(BaseModel):
    type: str  # 'github', 'gitlab', 'jenkins', 'azure', 'aws', 'kubernetes'


class IntegrationCreate(IntegrationBase):
    credentials: dict


class IntegrationResponse(IntegrationBase):
    id: int
    connected: bool

    class Config:
        from_attributes = True


class PolicyDecisionResponse(BaseModel):
    decision: str  # ALLOW, WARN, BLOCK
    risk_score: float
    risk_level: str
    confidence_score: float = 0.0
    reasoning: List[str] = []
    recommendations: List[str]
    message: str
    override_reason: Optional[str] = None
    alert_severity: Optional[str] = None
    affected_modules: List[str] = []
