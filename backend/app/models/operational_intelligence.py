from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, JSON, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class CorrelatedDeployment(Base):
    __tablename__ = "correlated_deployments"
    id = Column(Integer, primary_key=True, index=True)
    cluster_id = Column(String, index=True)
    primary_deployment_id = Column(Integer, ForeignKey("deployments.id"))
    secondary_deployment_id = Column(Integer, ForeignKey("deployments.id"))
    correlation_score = Column(Float)
    correlation_type = Column(String) # e.g. "cascading_failure", "dependency_chain"
    time_delta_seconds = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

class DeploymentRelationship(Base):
    __tablename__ = "deployment_relationships"
    id = Column(Integer, primary_key=True, index=True)
    source_deployment_id = Column(Integer, ForeignKey("deployments.id"))
    target_deployment_id = Column(Integer, ForeignKey("deployments.id"))
    relationship_type = Column(String)
    impact_score = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

class ServiceDependency(Base):
    __tablename__ = "service_dependencies"
    id = Column(Integer, primary_key=True, index=True)
    source_service = Column(String, index=True)
    target_service = Column(String, index=True)
    dependency_strength = Column(Float)
    failure_propagation_rate = Column(Float)
    last_observed = Column(DateTime, default=datetime.utcnow)

class AnomalyCluster(Base):
    __tablename__ = "anomaly_clusters"
    id = Column(Integer, primary_key=True, index=True)
    cluster_name = Column(String, index=True)
    root_cause_service = Column(String)
    severity_propagation = Column(JSON)
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)
    recurrence_count = Column(Integer, default=1)

class AnomalyPattern(Base):
    __tablename__ = "anomaly_patterns"
    id = Column(Integer, primary_key=True, index=True)
    cluster_id = Column(Integer, ForeignKey("anomaly_clusters.id"))
    pattern_signature = Column(String, unique=True, index=True)
    trigger_conditions = Column(JSON)
    escalation_path = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

class AnomalyMemory(Base):
    __tablename__ = "anomaly_memory"
    id = Column(Integer, primary_key=True, index=True)
    pattern_id = Column(Integer, ForeignKey("anomaly_patterns.id"))
    resolution_action = Column(String)
    success_rate = Column(Float)
    recorded_at = Column(DateTime, default=datetime.utcnow)

class OperationalMemory(Base):
    __tablename__ = "operational_memory"
    id = Column(Integer, primary_key=True, index=True)
    memory_type = Column(String, index=True) # "incident", "degradation", "success"
    context_hash = Column(String, unique=True, index=True)
    service_involved = Column(String, index=True)
    telemetry_snapshot = Column(JSON)
    lessons_learned = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

class ServiceOperationalHistory(Base):
    __tablename__ = "service_operational_history"
    id = Column(Integer, primary_key=True, index=True)
    service_name = Column(String, index=True)
    stability_score = Column(Float)
    MTTR_seconds = Column(Integer)
    degradation_frequency = Column(Float)
    recorded_at = Column(DateTime, default=datetime.utcnow)

class DeploymentMemory(Base):
    __tablename__ = "deployment_memory"
    id = Column(Integer, primary_key=True, index=True)
    deployment_id = Column(Integer, ForeignKey("deployments.id"))
    memory_context = Column(JSON)
    outcome_classification = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class ForecastingResult(Base):
    __tablename__ = "forecasting_results"
    id = Column(Integer, primary_key=True, index=True)
    target_service = Column(String, index=True)
    forecast_type = Column(String) # "instability_window", "degradation_risk"
    probability = Column(Float)
    predicted_time = Column(DateTime)
    features_used = Column(JSON)
    generated_at = Column(DateTime, default=datetime.utcnow)

class AdaptiveRecommendation(Base):
    __tablename__ = "adaptive_recommendations"
    id = Column(Integer, primary_key=True, index=True)
    target_service = Column(String, index=True)
    recommendation_type = Column(String)
    context_memory_id = Column(Integer, ForeignKey("operational_memory.id"), nullable=True)
    guidance = Column(Text)
    confidence_score = Column(Float)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
