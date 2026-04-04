from sqlalchemy import Column, Integer, Float, Boolean, JSON
from ..database import Base


class Settings(Base):
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, index=True)
    # We typically only have one row for global settings, or one per user/org
    risk_threshold = Column(Float, default=70.0, nullable=False)
    confidence_threshold = Column(Float, default=80.0, nullable=False)
    alerts_enabled = Column(Boolean, default=True, nullable=False)
    cluster_names = Column(JSON, default=list, nullable=False)
