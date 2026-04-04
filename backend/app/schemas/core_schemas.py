from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import List


class UserBase(BaseModel):
    email: EmailStr
    name: str


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: int

    class Config:
        from_attributes = True


class AlertBase(BaseModel):
    message: str
    severity: str
    read: bool = False


class AlertResponse(AlertBase):
    id: int
    timestamp: datetime

    class Config:
        from_attributes = True


class SettingsBase(BaseModel):
    risk_threshold: float
    confidence_threshold: float
    alerts_enabled: bool
    cluster_names: List[str]


class SettingsResponse(SettingsBase):
    id: int

    class Config:
        from_attributes = True
