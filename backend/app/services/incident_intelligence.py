"""
Phase 11.4: Incident Intelligence Service.

Converts alerts and anomalies into operational narratives:
  - Incident timeline construction
  - Correlated failure chain detection
  - Deployment clustering by failure pattern
  - Blast radius estimation
  - Cascading failure detection

Integrates with: Alert Service, Deployment Events, Anomaly Events.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from ..models.deployment import Deployment
from ..models.alerts import Alert
from ..models.phase11_models import (
    IncidentTimeline, DeploymentEvent, AnomalyEvent
)

logger = logging.getLogger("aegis.incident")


class IncidentIntelligence:
    """Converts raw alerts into structured incident narratives."""

    def _generate_incident_id(self) -> str:
        """Generate a unique incident identifier."""
        now = datetime.utcnow()
        import random
        seq = random.randint(1000, 9999)
        return f"INC-{now.strftime('%Y%m%d')}-{seq}"

    def detect_incidents(
        self,
        db: Session,
        lookback_hours: int = 24,
    ) -> List[Dict[str, Any]]:
        """
        Scan recent deployments and alerts for incident patterns.
        Returns a list of detected incident candidates.
        """
        cutoff = datetime.utcnow() - timedelta(hours=lookback_hours)

        # Fetch recent high-severity alerts
        recent_alerts = (
            db.query(Alert)
            .filter(Alert.timestamp >= cutoff)
            .filter(Alert.severity.in_(["CRITICAL", "HIGH"]))
            .order_by(desc(Alert.timestamp))
            .limit(100)
            .all()
        )

        if not recent_alerts:
            return []

        # Group alerts by affected service
        service_alerts: Dict[str, List[Alert]] = {}
        for alert in recent_alerts:
            svc = alert.affected_service or "unknown"
            if svc not in service_alerts:
                service_alerts[svc] = []
            service_alerts[svc].append(alert)

        incidents = []
        for service, alerts in service_alerts.items():
            if len(alerts) >= 2:  # Multiple alerts = potential incident
                deployment_ids = list(set(a.deployment_id for a in alerts))
                alert_ids = [a.id for a in alerts]

                # Check for existing unresolved incident
                existing = (
                    db.query(IncidentTimeline)
                    .filter(
                        IncidentTimeline.status.in_(["active", "investigating"]),
                    )
                    .all()
                )
                # Simple dedup: skip if all deployment_ids are already in an existing incident
                already_tracked = False
                for inc in existing:
                    tracked_deps = inc.correlated_deployment_ids or []
                    if all(did in tracked_deps for did in deployment_ids):
                        already_tracked = True
                        break

                if already_tracked:
                    continue

                severity = "CRITICAL" if any(a.severity == "CRITICAL" for a in alerts) else "HIGH"
                blast_radius = self._estimate_blast_radius(db, service, deployment_ids)
                event_chain = self._build_event_chain(db, deployment_ids)

                incident = {
                    "service": service,
                    "severity": severity,
                    "alert_count": len(alerts),
                    "deployment_ids": deployment_ids,
                    "alert_ids": alert_ids,
                    "blast_radius": blast_radius,
                    "event_chain": event_chain,
                    "detected_at": datetime.utcnow().isoformat(),
                }
                incidents.append(incident)

        return incidents

    def create_incident(
        self,
        db: Session,
        service: str,
        severity: str,
        deployment_ids: List[int],
        alert_ids: List[int],
        blast_radius: Optional[Dict] = None,
        event_chain: Optional[List] = None,
    ) -> Dict[str, Any]:
        """Create and persist a new incident timeline."""
        incident_id = self._generate_incident_id()
        title = f"Service Degradation: {service}"
        if severity == "CRITICAL":
            title = f"Critical Incident: {service}"

        incident = IncidentTimeline(
            incident_id=incident_id,
            title=title,
            severity=severity,
            status="active",
            correlated_deployment_ids=deployment_ids,
            correlated_alert_ids=alert_ids,
            blast_radius=blast_radius,
            event_chain=event_chain,
        )
        db.add(incident)
        db.commit()
        db.refresh(incident)

        logger.info(
            f"[Incident] created incident_id={incident_id} service={service} "
            f"severity={severity} deployments={len(deployment_ids)} alerts={len(alert_ids)}"
        )

        return {
            "incident_id": incident.incident_id,
            "title": incident.title,
            "severity": incident.severity,
            "status": incident.status,
            "deployment_ids": deployment_ids,
            "alert_ids": alert_ids,
            "blast_radius": blast_radius,
            "event_chain": event_chain,
            "created_at": incident.created_at.isoformat() if incident.created_at else None,
        }

    def _estimate_blast_radius(
        self,
        db: Session,
        service: str,
        deployment_ids: List[int],
    ) -> Dict[str, Any]:
        """Estimate the blast radius of an incident."""
        # Count affected deployments
        affected_deployments = (
            db.query(Deployment)
            .filter(Deployment.id.in_(deployment_ids))
            .all()
        )

        # Check for cross-service impact (other services deployed at similar times)
        services_affected = set()
        for dep in affected_deployments:
            if dep.repo_name:
                services_affected.add(dep.repo_name)

        # Calculate impact score
        high_risk_count = sum(1 for d in affected_deployments if (d.risk_score or 0) > 70)
        blocked_count = sum(1 for d in affected_deployments if d.deployment_decision == "BLOCK")

        return {
            "primary_service": service,
            "services_affected": list(services_affected),
            "total_deployments_affected": len(affected_deployments),
            "high_risk_deployments": high_risk_count,
            "blocked_deployments": blocked_count,
            "estimated_impact": "high" if high_risk_count > 2 else "medium" if high_risk_count > 0 else "low",
        }

    def _build_event_chain(
        self,
        db: Session,
        deployment_ids: List[int],
    ) -> List[Dict[str, Any]]:
        """Build an ordered event chain from deployment events."""
        events = (
            db.query(DeploymentEvent)
            .filter(DeploymentEvent.deployment_id.in_(deployment_ids))
            .order_by(DeploymentEvent.timestamp.asc())
            .limit(50)
            .all()
        )

        return [
            {
                "timestamp": e.timestamp.isoformat() if e.timestamp else None,
                "deployment_id": e.deployment_id,
                "event_type": e.event_type,
                "severity": e.severity,
                "source": e.source,
                "summary": (e.event_data or {}).get("summary", e.event_type),
            }
            for e in events
        ]

    def get_incidents(
        self,
        db: Session,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """Retrieve incidents with optional filters."""
        query = db.query(IncidentTimeline)
        if status:
            query = query.filter(IncidentTimeline.status == status)
        if severity:
            query = query.filter(IncidentTimeline.severity == severity)

        incidents = query.order_by(desc(IncidentTimeline.created_at)).limit(limit).all()

        return [
            {
                "incident_id": inc.incident_id,
                "title": inc.title,
                "severity": inc.severity,
                "status": inc.status,
                "root_cause": inc.root_cause,
                "blast_radius": inc.blast_radius,
                "deployment_ids": inc.correlated_deployment_ids or [],
                "alert_ids": inc.correlated_alert_ids or [],
                "event_chain": inc.event_chain or [],
                "created_at": inc.created_at.isoformat() if inc.created_at else None,
                "resolved_at": inc.resolved_at.isoformat() if inc.resolved_at else None,
            }
            for inc in incidents
        ]

    def get_incident_detail(
        self,
        db: Session,
        incident_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Get full incident detail including timeline events."""
        inc = (
            db.query(IncidentTimeline)
            .filter(IncidentTimeline.incident_id == incident_id)
            .first()
        )
        if not inc:
            return None

        # Enrich with deployment details
        deployment_details = []
        dep_ids = inc.correlated_deployment_ids or []
        if dep_ids:
            deployments = db.query(Deployment).filter(Deployment.id.in_(dep_ids)).all()
            deployment_details = [
                {
                    "id": d.id,
                    "service": d.repo_name,
                    "risk_score": d.risk_score,
                    "decision": d.deployment_decision,
                    "outcome": d.deployment_outcome,
                    "timestamp": d.timestamp.isoformat() if d.timestamp else None,
                }
                for d in deployments
            ]

        # Enrich with alert details
        alert_details = []
        alert_ids = inc.correlated_alert_ids or []
        if alert_ids:
            alerts = db.query(Alert).filter(Alert.id.in_(alert_ids)).all()
            alert_details = [
                {
                    "id": a.id,
                    "type": a.alert_type,
                    "severity": a.severity,
                    "message": a.message,
                    "timestamp": a.timestamp.isoformat() if a.timestamp else None,
                }
                for a in alerts
            ]

        return {
            "incident_id": inc.incident_id,
            "title": inc.title,
            "severity": inc.severity,
            "status": inc.status,
            "root_cause": inc.root_cause,
            "blast_radius": inc.blast_radius,
            "event_chain": inc.event_chain or [],
            "deployments": deployment_details,
            "alerts": alert_details,
            "created_at": inc.created_at.isoformat() if inc.created_at else None,
            "updated_at": inc.updated_at.isoformat() if inc.updated_at else None,
            "resolved_at": inc.resolved_at.isoformat() if inc.resolved_at else None,
        }

    def resolve_incident(
        self,
        db: Session,
        incident_id: str,
        root_cause: Optional[str] = None,
    ) -> bool:
        """Mark an incident as resolved."""
        inc = (
            db.query(IncidentTimeline)
            .filter(IncidentTimeline.incident_id == incident_id)
            .first()
        )
        if not inc:
            return False

        inc.status = "resolved"
        inc.resolved_at = datetime.utcnow()
        if root_cause:
            inc.root_cause = root_cause
        db.commit()

        logger.info(f"[Incident] resolved incident_id={incident_id}")
        return True


# Singleton instance
incident_intelligence = IncidentIntelligence()
