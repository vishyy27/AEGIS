from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_
from datetime import datetime, timedelta
from app.models.deployment import Deployment
from app.models.operational_intelligence import ServiceOperationalHistory
import json

class TemporalIntelligenceEngine:
    def __init__(self):
        pass

    def analyze_service_drift(self, db: Session, service_name: str, days_back: int = 7):
        time_window = datetime.utcnow() - timedelta(days=days_back)
        
        # Get deployments for this service
        deployments = db.query(Deployment).filter(
            and_(
                Deployment.repo_name == service_name,
                Deployment.timestamp >= time_window
            )
        ).order_by(Deployment.timestamp.asc()).all()
        
        if not deployments:
            return None

        failed_count = sum(1 for d in deployments if d.status == "failed")
        total_count = len(deployments)
        
        # Simple drift calc
        failure_rate = failed_count / total_count if total_count > 0 else 0
        stability_score = max(0.0, 100.0 - (failure_rate * 100))
        
        # Save historical snapshot
        history = ServiceOperationalHistory(
            service_name=service_name,
            stability_score=stability_score,
            degradation_frequency=failure_rate,
            MTTR_seconds=3600 # Placeholder for mean time to recovery
        )
        db.add(history)
        db.commit()
        db.refresh(history)
        
        return history

temporal_intelligence_engine = TemporalIntelligenceEngine()
