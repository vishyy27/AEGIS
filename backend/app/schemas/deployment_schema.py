from pydantic import BaseModel
from datetime import datetime


class DeploymentBase(BaseModel):
    service: str
    environment: str


class DeploymentCreate(DeploymentBase):
    pass


class DeploymentResponse(DeploymentBase):
    id: int
    risk_score: float
    status: str
    timestamp: datetime

    class Config:
        from_attributes = True
