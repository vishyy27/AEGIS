from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from ..database import Base

class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, index=True)
    deployment_id = Column(Integer, ForeignKey("deployments.id"))
    message = Column(Text)
    priority = Column(String)
    category = Column(String)
    affected_module = Column(String, nullable=True)
    source_engine = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    deployment = relationship("Deployment", back_populates="recommendations")
