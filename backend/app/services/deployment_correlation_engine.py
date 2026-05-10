from sqlalchemy.orm import Session
from sqlalchemy import select, and_, func
from datetime import datetime, timedelta
from app.models.operational_intelligence import CorrelatedDeployment, DeploymentRelationship, ServiceDependency
from app.models.deployment import Deployment
import json

class DeploymentCorrelationEngine:
    def __init__(self):
        pass

    def analyze_correlation(self, db: Session, target_deployment: Deployment):
        # Find deployments in last hour
        time_window = target_deployment.timestamp - timedelta(hours=1)
        recent_deployments = db.query(Deployment).filter(
            and_(
                Deployment.timestamp >= time_window,
                Deployment.id != target_deployment.id
            )
        ).all()
        
        correlations = []
        for d in recent_deployments:
            score = 0.0
            type_str = "temporal"
            if d.repo_name != target_deployment.repo_name:
                score += 0.5
                type_str = "cross_service_temporal"
            if d.status == "failed" and target_deployment.status == "failed":
                score += 0.8
                type_str = "cascading_failure"
            
            if score > 0.0:
                corr = CorrelatedDeployment(
                    primary_deployment_id=target_deployment.id,
                    secondary_deployment_id=d.id,
                    correlation_score=score,
                    correlation_type=type_str,
                    time_delta_seconds=int((target_deployment.timestamp - d.timestamp).total_seconds())
                )
                db.add(corr)
                correlations.append(corr)
        
        db.commit()
        return correlations

    def build_dependency_graph(self, db: Session):
        # Stub for topology mapping
        return db.query(ServiceDependency).all()

deployment_correlation_engine = DeploymentCorrelationEngine()
