"""
Phase 11.2: Event Stream Service.

Bridges all AEGIS subsystems → WebSocket topics.
Every deployment analysis, policy decision, alert, and anomaly
emits structured events for real-time frontend consumption.

Also persists events to the deployment_events table for replay capability.
"""

import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session

from ..models.phase11_models import DeploymentEvent, AnomalyEvent
from .websocket_manager import ws_manager

logger = logging.getLogger("aegis.events")


class EventStreamService:
    """Emits and persists deployment lifecycle events."""

    # ---- Event emission (WebSocket broadcast) ----

    async def emit_deployment_event(
        self,
        deployment_id: int,
        event_type: str,
        event_data: Dict[str, Any],
        severity: str = "INFO",
        source: str = "system",
        db: Optional[Session] = None,
    ):
        """Emit a deployment lifecycle event to WebSocket and persist to DB."""
        event = {
            "type": "deployment_event",
            "deployment_id": deployment_id,
            "event_type": event_type,
            "event_data": event_data,
            "severity": severity,
            "source": source,
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Broadcast to WebSocket subscribers
        await ws_manager.broadcast_to_topic("deployments", event)
        await ws_manager.broadcast_to_topic("telemetry", event)

        # Persist to database
        if db:
            try:
                db_event = DeploymentEvent(
                    deployment_id=deployment_id,
                    event_type=event_type,
                    event_data=event_data,
                    severity=severity,
                    source=source,
                )
                db.add(db_event)
                db.commit()
            except Exception as e:
                logger.warning(f"[Events] persist_failed event_type={event_type} error={e}")

        logger.debug(f"[Events] emitted deployment_id={deployment_id} type={event_type}")

    async def emit_alert_event(
        self,
        alert_data: Dict[str, Any],
        db: Optional[Session] = None,
    ):
        """Emit an alert event to WebSocket subscribers."""
        event = {
            "type": "alert_event",
            "alert": alert_data,
            "timestamp": datetime.utcnow().isoformat(),
        }
        await ws_manager.broadcast_to_topic("alerts", event)
        
        # Also persist as deployment event if we have a deployment_id
        deployment_id = alert_data.get("deployment_id")
        if deployment_id and db:
            try:
                db_event = DeploymentEvent(
                    deployment_id=deployment_id,
                    event_type="alert_fired",
                    event_data=alert_data,
                    severity=alert_data.get("severity", "WARNING"),
                    source="alert_service",
                )
                db.add(db_event)
                db.commit()
            except Exception as e:
                logger.warning(f"[Events] alert_persist_failed error={e}")

    async def emit_policy_decision(
        self,
        deployment_id: int,
        decision_data: Dict[str, Any],
        db: Optional[Session] = None,
    ):
        """Emit a policy decision event to WebSocket subscribers."""
        event = {
            "type": "policy_decision",
            "deployment_id": deployment_id,
            "decision": decision_data,
            "timestamp": datetime.utcnow().isoformat(),
        }
        await ws_manager.broadcast_to_topic("policy", event)
        await ws_manager.broadcast_to_topic("telemetry", event)

        if db:
            try:
                db_event = DeploymentEvent(
                    deployment_id=deployment_id,
                    event_type="policy_decided",
                    event_data=decision_data,
                    severity="INFO" if decision_data.get("decision") == "ALLOW" else "WARNING",
                    source="policy_engine",
                )
                db.add(db_event)
                db.commit()
            except Exception as e:
                logger.warning(f"[Events] policy_persist_failed error={e}")

    async def emit_anomaly_event(
        self,
        service_name: str,
        anomaly_type: str,
        description: str,
        impact_score: float,
        deployment_id: Optional[int] = None,
        contributing_features: Optional[Dict] = None,
        db: Optional[Session] = None,
    ):
        """Emit and persist an anomaly detection event."""
        event = {
            "type": "anomaly_event",
            "service_name": service_name,
            "anomaly_type": anomaly_type,
            "description": description,
            "impact_score": impact_score,
            "deployment_id": deployment_id,
            "contributing_features": contributing_features,
            "timestamp": datetime.utcnow().isoformat(),
        }
        await ws_manager.broadcast_to_topic("telemetry", event)
        await ws_manager.broadcast_to_topic("alerts", event)

        if db:
            try:
                anomaly = AnomalyEvent(
                    deployment_id=deployment_id,
                    service_name=service_name,
                    anomaly_type=anomaly_type,
                    description=description,
                    impact_score=impact_score,
                    contributing_features=contributing_features,
                )
                db.add(anomaly)
                db.commit()
            except Exception as e:
                logger.warning(f"[Events] anomaly_persist_failed error={e}")

    async def emit_incident_event(
        self,
        incident_data: Dict[str, Any],
    ):
        """Emit an incident intelligence event."""
        event = {
            "type": "incident_event",
            "incident": incident_data,
            "timestamp": datetime.utcnow().isoformat(),
        }
        await ws_manager.broadcast_to_topic("incidents", event)
        await ws_manager.broadcast_to_topic("telemetry", event)

    async def emit_simulation_result(
        self,
        simulation_data: Dict[str, Any],
    ):
        """Emit a simulation result event."""
        event = {
            "type": "simulation_result",
            "simulation": simulation_data,
            "timestamp": datetime.utcnow().isoformat(),
        }
        await ws_manager.broadcast_to_topic("telemetry", event)

    async def emit_system_status(self):
        """Emit current system telemetry status."""
        status = {
            "type": "system_status",
            "active_connections": ws_manager.active_connections,
            "topic_stats": ws_manager.topic_stats,
            "timestamp": datetime.utcnow().isoformat(),
        }
        await ws_manager.broadcast_to_topic("telemetry", status)

    # ---- Event retrieval (for replay and history) ----

    def get_deployment_events(
        self,
        db: Session,
        deployment_id: int,
        event_types: Optional[List[str]] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Retrieve persisted deployment events for replay."""
        query = db.query(DeploymentEvent).filter(
            DeploymentEvent.deployment_id == deployment_id
        )
        if event_types:
            query = query.filter(DeploymentEvent.event_type.in_(event_types))
        
        events = query.order_by(DeploymentEvent.timestamp.asc()).limit(limit).all()
        
        return [
            {
                "id": e.id,
                "deployment_id": e.deployment_id,
                "event_type": e.event_type,
                "event_data": e.event_data,
                "severity": e.severity,
                "source": e.source,
                "timestamp": e.timestamp.isoformat() if e.timestamp else None,
            }
            for e in events
        ]

    def get_recent_events(
        self,
        db: Session,
        limit: int = 50,
        event_types: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieve recent deployment events across all deployments."""
        query = db.query(DeploymentEvent)
        if event_types:
            query = query.filter(DeploymentEvent.event_type.in_(event_types))

        events = query.order_by(DeploymentEvent.timestamp.desc()).limit(limit).all()

        return [
            {
                "id": e.id,
                "deployment_id": e.deployment_id,
                "event_type": e.event_type,
                "event_data": e.event_data,
                "severity": e.severity,
                "source": e.source,
                "timestamp": e.timestamp.isoformat() if e.timestamp else None,
            }
            for e in events
        ]


# Singleton instance
event_stream = EventStreamService()
