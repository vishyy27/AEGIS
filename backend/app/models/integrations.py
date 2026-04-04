from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from ..database import Base


class Integration(Base):
    __tablename__ = "integrations"

    id = Column(Integer, primary_key=True, index=True)
    provider = Column(String, nullable=False)  # "github", "gitlab", "jenkins"
    repo_name = Column(String, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
