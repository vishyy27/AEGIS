from pydantic import BaseModel
from typing import Dict, List, Optional


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
    # Phase 9.3 Meta-Learning fields
    decision_score: Optional[float] = None
    signal_weights: Optional[Dict[str, float]] = None
    anomaly_flags: List[str] = []
    policy_version: Optional[str] = None
    # Explainability & recommendations (existing)
    reasoning: List[str] = []
    recommendations: List[str]
    message: str
    override_reason: Optional[str] = None
    alert_severity: Optional[str] = None
    affected_modules: List[str] = []
