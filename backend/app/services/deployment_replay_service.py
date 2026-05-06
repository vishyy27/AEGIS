"""
Phase 11.5: Deployment Replay Service.
Provides timeline replay of historical deployments.
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc

from ..models.deployment import Deployment
from ..models.alerts import Alert
from ..models.phase11_models import DeploymentEvent, AnomalyEvent, PolicyExplanation

logger = logging.getLogger("aegis.replay")


class DeploymentReplayService:
    def get_replay_timeline(self, db: Session, deployment_id: int) -> Optional[Dict[str, Any]]:
        deployment = db.query(Deployment).filter(Deployment.id == deployment_id).first()
        if not deployment:
            return None

        events = self._get_events(db, deployment_id)
        alerts = self._get_alerts(db, deployment_id)
        anomalies = self._get_anomalies(db, deployment_id)
        explanation = self._get_explanation(db, deployment_id)

        timeline_items = []
        for e in events:
            timeline_items.append({"type": "event", "timestamp": e["timestamp"], "data": e})
        for a in alerts:
            timeline_items.append({"type": "alert", "timestamp": a["timestamp"], "data": a})
        for an in anomalies:
            timeline_items.append({"type": "anomaly", "timestamp": an["detected_at"], "data": an})

        timeline_items.sort(key=lambda x: x["timestamp"] or "")

        base_time = deployment.timestamp
        if base_time:
            for item in timeline_items:
                ts = item.get("timestamp")
                if ts:
                    try:
                        dt = datetime.fromisoformat(ts)
                        item["relative_seconds"] = round((dt - base_time).total_seconds(), 2)
                    except (ValueError, TypeError):
                        item["relative_seconds"] = 0
                else:
                    item["relative_seconds"] = 0

        return {
            "deployment_id": deployment_id,
            "service": deployment.repo_name,
            "risk_score": deployment.risk_score,
            "risk_level": deployment.risk_level,
            "decision": deployment.deployment_decision,
            "outcome": deployment.deployment_outcome,
            "ml_probability": deployment.ml_prediction_prob,
            "confidence": deployment.policy_confidence_score,
            "started_at": deployment.timestamp.isoformat() if deployment.timestamp else None,
            "total_events": len(timeline_items),
            "timeline": timeline_items,
            "explanation": explanation,
        }

    def get_replay_list(self, db: Session, service: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        query = db.query(Deployment)
        if service:
            query = query.filter(Deployment.repo_name == service)
        deployments = query.order_by(desc(Deployment.timestamp)).limit(limit).all()
        results = []
        for d in deployments:
            event_count = db.query(DeploymentEvent).filter(DeploymentEvent.deployment_id == d.id).count()
            alert_count = db.query(Alert).filter(Alert.deployment_id == d.id).count()
            results.append({
                "deployment_id": d.id, "service": d.repo_name,
                "risk_score": d.risk_score, "risk_level": d.risk_level,
                "decision": d.deployment_decision, "outcome": d.deployment_outcome,
                "event_count": event_count, "alert_count": alert_count,
                "timestamp": d.timestamp.isoformat() if d.timestamp else None,
                "has_replay_data": event_count > 0,
            })
        return results

    def _get_events(self, db: Session, deployment_id: int) -> List[Dict]:
        events = db.query(DeploymentEvent).filter(DeploymentEvent.deployment_id == deployment_id).order_by(DeploymentEvent.timestamp.asc()).all()
        return [{"id": e.id, "event_type": e.event_type, "event_data": e.event_data, "severity": e.severity, "source": e.source, "timestamp": e.timestamp.isoformat() if e.timestamp else None} for e in events]

    def _get_alerts(self, db: Session, deployment_id: int) -> List[Dict]:
        alerts = db.query(Alert).filter(Alert.deployment_id == deployment_id).order_by(Alert.timestamp.asc()).all()
        return [{"id": a.id, "alert_type": a.alert_type, "severity": a.severity, "message": a.message, "timestamp": a.timestamp.isoformat() if a.timestamp else None} for a in alerts]

    def _get_anomalies(self, db: Session, deployment_id: int) -> List[Dict]:
        anomalies = db.query(AnomalyEvent).filter(AnomalyEvent.deployment_id == deployment_id).all()
        return [{"id": a.id, "anomaly_type": a.anomaly_type, "description": a.description, "impact_score": a.impact_score, "contributing_features": a.contributing_features, "detected_at": a.detected_at.isoformat() if a.detected_at else None} for a in anomalies]

    def _get_explanation(self, db: Session, deployment_id: int) -> Optional[Dict]:
        exp = db.query(PolicyExplanation).filter(PolicyExplanation.deployment_id == deployment_id).order_by(desc(PolicyExplanation.created_at)).first()
        if not exp:
            return None
        return {"decision": exp.decision, "waterfall_stages": exp.waterfall_stages, "feature_impacts": exp.feature_impacts, "static_weight": exp.static_weight, "ml_weight": exp.ml_weight, "confidence_breakdown": exp.confidence_breakdown}

replay_service = DeploymentReplayService()
