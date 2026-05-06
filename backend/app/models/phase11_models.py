"""
Phase 11: New database models for AI-native real-time DevOps platform.

Tables:
  - DeploymentEvent: Granular event log for replay and telemetry streaming
  - AnomalyEvent: Detected anomalies with severity and contribution data
  - IncidentTimeline: Correlated incident narratives
  - SimulationRun: Synthetic deployment simulation records
  - PolicyExplanation: XAI policy waterfall snapshots
  - ServiceProfile: Fleet-wide service health profiles
  - ChatSession: AI assistant conversation sessions
  - ChatMessage: Individual assistant messages
  - AuditLog: Enterprise audit trail
"""

from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, JSON
)
from sqlalchemy.orm import relationship
from datetime import datetime
from ..database import Base


class DeploymentEvent(Base):
    """Granular event log for every deployment lifecycle event.
    Used by: Telemetry streaming, Replay engine, Incident correlation."""
    __tablename__ = "deployment_events"

    id = Column(Integer, primary_key=True, index=True)
    deployment_id = Column(Integer, ForeignKey("deployments.id"), index=True, nullable=False)
    event_type = Column(String, nullable=False, index=True)  # webhook_received, analysis_started, ml_predicted, policy_decided, alert_fired, completed, failed
    event_data = Column(JSON, nullable=True)  # Flexible payload per event type
    severity = Column(String, nullable=True)  # INFO, WARNING, ERROR, CRITICAL
    source = Column(String, nullable=True)  # ml_engine, policy_engine, alert_service, webhook, user
    timestamp = Column(DateTime, default=datetime.utcnow, index=True, nullable=False)


class AnomalyEvent(Base):
    """Detected anomaly events with impact scoring for XAI and incident intelligence."""
    __tablename__ = "anomaly_events"

    id = Column(Integer, primary_key=True, index=True)
    deployment_id = Column(Integer, ForeignKey("deployments.id"), index=True, nullable=True)
    service_name = Column(String, index=True, nullable=False)
    anomaly_type = Column(String, nullable=False)  # drift, spike, threshold_breach, pattern_deviation
    description = Column(Text, nullable=True)
    impact_score = Column(Float, nullable=True)  # 0.0–1.0
    contributing_features = Column(JSON, nullable=True)  # Feature breakdown for XAI
    resolved = Column(Boolean, default=False)
    resolution_note = Column(Text, nullable=True)
    detected_at = Column(DateTime, default=datetime.utcnow, index=True, nullable=False)
    resolved_at = Column(DateTime, nullable=True)


class IncidentTimeline(Base):
    """Correlated incident narratives linking deployments, alerts, and anomalies."""
    __tablename__ = "incident_timelines"

    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(String, unique=True, index=True, nullable=False)  # INC-YYYYMMDD-XXXX
    title = Column(String, nullable=False)
    severity = Column(String, nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    status = Column(String, default="active")  # active, investigating, resolved, closed
    root_cause = Column(Text, nullable=True)
    blast_radius = Column(JSON, nullable=True)  # {"services": [...], "deployments": [...], "estimated_impact": "..."}
    correlated_deployment_ids = Column(JSON, nullable=True)  # [deployment_id, ...]
    correlated_alert_ids = Column(JSON, nullable=True)  # [alert_id, ...]
    correlated_anomaly_ids = Column(JSON, nullable=True)  # [anomaly_id, ...]
    event_chain = Column(JSON, nullable=True)  # Ordered list of events
    created_at = Column(DateTime, default=datetime.utcnow, index=True, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)


class SimulationRun(Base):
    """Synthetic deployment simulation records for the Simulation Lab."""
    __tablename__ = "simulation_runs"

    id = Column(Integer, primary_key=True, index=True)
    simulation_name = Column(String, nullable=True)
    input_parameters = Column(JSON, nullable=False)  # The synthetic deployment payload
    projected_risk_score = Column(Float, nullable=True)
    projected_risk_level = Column(String, nullable=True)
    ml_failure_probability = Column(Float, nullable=True)
    policy_decision = Column(String, nullable=True)  # ALLOW, WARN, BLOCK
    policy_reasoning = Column(JSON, nullable=True)  # List of reasoning strings
    predicted_alerts = Column(JSON, nullable=True)  # Predicted alert types
    confidence_score = Column(Float, nullable=True)
    xai_breakdown = Column(JSON, nullable=True)  # Feature impact breakdown
    created_by = Column(String, nullable=True)  # User/API key
    created_at = Column(DateTime, default=datetime.utcnow, index=True, nullable=False)


class PolicyExplanation(Base):
    """XAI policy waterfall snapshots for explainability."""
    __tablename__ = "policy_explanations"

    id = Column(Integer, primary_key=True, index=True)
    deployment_id = Column(Integer, ForeignKey("deployments.id"), index=True, nullable=False)
    decision = Column(String, nullable=False)
    waterfall_stages = Column(JSON, nullable=False)  # Ordered list of stage evaluations
    feature_impacts = Column(JSON, nullable=True)  # Feature name → impact score
    static_weight = Column(Float, nullable=True)  # Weight of static rules in final decision
    ml_weight = Column(Float, nullable=True)  # Weight of ML in final decision
    confidence_breakdown = Column(JSON, nullable=True)  # Per-signal confidence contributions
    anomaly_contributions = Column(JSON, nullable=True)  # Anomaly impact breakdown
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class ServiceProfile(Base):
    """Fleet-wide service health and risk profiles."""
    __tablename__ = "service_profiles"

    id = Column(Integer, primary_key=True, index=True)
    service_name = Column(String, unique=True, index=True, nullable=False)
    total_deployments = Column(Integer, default=0)
    total_failures = Column(Integer, default=0)
    avg_risk_score = Column(Float, nullable=True)
    max_risk_score = Column(Float, nullable=True)
    deployment_frequency_7d = Column(Integer, default=0)
    failure_rate = Column(Float, nullable=True)  # 0.0–1.0
    stability_score = Column(Float, nullable=True)  # 0.0–100.0 (higher = more stable)
    risk_trend = Column(String, nullable=True)  # improving, stable, degrading
    last_deployment_at = Column(DateTime, nullable=True)
    last_failure_at = Column(DateTime, nullable=True)
    health_status = Column(String, default="unknown")  # healthy, warning, critical, unknown
    profile_metadata = Column(JSON, nullable=True)  # Extensible metadata
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ChatSession(Base):
    """AI assistant conversation sessions."""
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, unique=True, index=True, nullable=False)
    title = Column(String, nullable=True)
    user_id = Column(String, nullable=True)  # Future RBAC integration
    context_deployment_id = Column(Integer, ForeignKey("deployments.id"), nullable=True)
    context_service = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")


class ChatMessage(Base):
    """Individual AI assistant messages."""
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, ForeignKey("chat_sessions.session_id"), index=True, nullable=False)
    role = Column(String, nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    context_data = Column(JSON, nullable=True)  # Attached deployment/alert context
    reasoning_chain = Column(JSON, nullable=True)  # XAI reasoning for assistant responses
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    session = relationship("ChatSession", back_populates="messages")


class AuditLog(Base):
    """Enterprise audit trail for all significant operations."""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    action = Column(String, nullable=False, index=True)  # deployment.created, policy.overridden, simulation.run, etc.
    actor = Column(String, nullable=True)  # User or system identifier
    resource_type = Column(String, nullable=True)  # deployment, alert, incident, simulation
    resource_id = Column(String, nullable=True)
    details = Column(JSON, nullable=True)
    ip_address = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True, nullable=False)
