from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime
from ..database import Base


class Deployment(Base):
    __tablename__ = "deployments"

    id = Column(Integer, primary_key=True, index=True)
    service = Column(String, index=True)
    environment = Column(String)
    risk_score = Column(Float)
    status = Column(String)
    repo_name = Column(String, index=True)
    commit_count = Column(Integer, default=0)
    files_changed = Column(Integer, default=0)
    code_churn = Column(Integer, default=0)
    test_coverage = Column(Float, default=100.0)
    dependency_updates = Column(Integer, default=0)
    historical_failures = Column(Integer, default=0)
    deployment_frequency = Column(Integer, default=0)
    risk_score = Column(Float)
    risk_level = Column(String)
    
    # Phase 3 Expansion Columns
    change_risk_score = Column(Float, nullable=True)
    risk_categories = Column(String, nullable=True)
    sensitive_files = Column(String, nullable=True)
    churn_ratio = Column(Float, nullable=True)
    commit_density = Column(Float, nullable=True)
    
    # Phase 4 CI/CD Integration Columns
    pipeline_source = Column(String, nullable=True)  # github, gitlab, jenkins, generic
    branch_name = Column(String, nullable=True)
    commit_hash = Column(String, nullable=True)
    deployment_environment = Column(String, nullable=True)
    
    timestamp = Column(DateTime, default=datetime.utcnow)
