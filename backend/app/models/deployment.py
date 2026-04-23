from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.orm import relationship
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
    
    # Phase 6 Context-Aware AI Recommendation Engine Columns
    primary_recommendation_priority = Column(String, nullable=True)
    primary_recommendation_category = Column(String, nullable=True)
    
    # Phase 7 Deployment Stability Analytics Columns
    deployment_outcome = Column(String, nullable=True)
    incident_flag = Column(Boolean, default=False)
    
    # Phase 8 Machine Learning Columns
    ml_prediction_prob = Column(Float, nullable=True)
    ml_used = Column(Boolean, default=False)
    
    # Phase 8.2 Production ML Extensions
    failure_rate_last_10 = Column(Float, nullable=True)
    avg_risk_last_5 = Column(Float, nullable=True)
    has_db_migration = Column(Boolean, nullable=True, default=False)
    has_auth_changes = Column(Boolean, nullable=True, default=False)
    has_payment_changes = Column(Boolean, nullable=True, default=False)
    has_core_module_changes = Column(Boolean, nullable=True, default=False)
    model_version = Column(String, nullable=True)
    prediction_confidence_score = Column(Float, nullable=True)
    
    # Phase 8.3 Machine Learning Intelligence & XAI
    prediction_correct = Column(Boolean, nullable=True)
    predicted_failure = Column(Boolean, nullable=True)
    actual_outcome = Column(Boolean, nullable=True)
    feature_signature = Column(String, nullable=True)
    drift_detected = Column(Boolean, default=False)
    drift_score = Column(Float, nullable=True)
    low_confidence_flag = Column(Boolean, default=False)
    
    timestamp = Column(DateTime, default=datetime.utcnow)

    # Relationships
    recommendations = relationship("Recommendation", back_populates="deployment")
