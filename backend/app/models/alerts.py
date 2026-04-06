from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from datetime import datetime
from ..database import Base


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    deployment_id = Column(
        Integer, ForeignKey("deployments.id"), index=True, nullable=False
    )
    alert_type = Column(String, nullable=False)
    severity = Column(String, nullable=False)
    message = Column(String, nullable=False)
    incident_pattern = Column(String, nullable=True)
    affected_service = Column(String, nullable=True, index=True)
    status = Column(String, default="active", nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
