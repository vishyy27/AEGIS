from sqlalchemy.orm import Session
from sqlalchemy import func, case, extract
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from ..models.deployment import Deployment
from ..models.alerts import Alert


def get_window_start(window_hours: int) -> datetime:
    return datetime.utcnow() - timedelta(hours=window_hours)


def calculate_success_rate(db: Session, window_hours: int = 24) -> float:
    window_start = get_window_start(window_hours)
    
    total_deployments = db.query(Deployment).filter(Deployment.timestamp >= window_start).count()
    if total_deployments == 0:
        return 100.0  # Default if no deployments exist
        
    failures = db.query(Deployment).filter(
        Deployment.timestamp >= window_start,
        (Deployment.status.in_(["failure", "error", "rollback"]) | 
         Deployment.deployment_outcome.in_(["failure", "error", "rollback"]))
    ).count()
    
    success_rate = ((total_deployments - failures) / total_deployments) * 100
    return round(success_rate, 2)


def compute_service_stability(db: Session, service: Optional[str] = None, window_hours: int = 168) -> float:
    window_start = get_window_start(window_hours)
    
    base_query = db.query(Deployment).filter(Deployment.timestamp >= window_start)
    if service:
        base_query = base_query.filter(Deployment.repo_name == service)
        
    deployments = base_query.all()
    if not deployments:
        return 100.0
        
    score = 100.0
    
    # -10 per deployment failure
    failures = sum(1 for d in deployments if d.status in ["failure", "error", "rollback"] or d.deployment_outcome in ["failure", "error", "rollback"])
    score -= (failures * 10)
    
    # -2 per high risk deployment
    high_risks = sum(1 for d in deployments if d.risk_score is not None and d.risk_score >= 70.0)
    score -= (high_risks * 2)
    
    # -5 per incident flag (critical failure indicator)
    incidents = sum(1 for d in deployments if d.incident_flag)
    score -= (incidents * 5)
        
    return max(0.0, round(score, 2))


def get_all_services_stability(db: Session, window_hours: int = 168) -> List[Dict[str, Any]]:
    # Get all distinct services in the window
    window_start = get_window_start(window_hours)
    services = db.query(Deployment.repo_name).filter(
        Deployment.timestamp >= window_start,
        Deployment.repo_name.isnot(None)
    ).distinct().all()
    
    results = []
    for (svc,) in services:
        stability = compute_service_stability(db, service=svc, window_hours=window_hours)
        results.append({
            "service": svc,
            "stability_index": stability
        })
        
    # Sort by stability ascending (worst first)
    return sorted(results, key=lambda x: x["stability_index"])


def detect_risk_trends(db: Session, window_hours: int = 720) -> List[Dict[str, Any]]:
    window_start = get_window_start(window_hours)
    
    # Group by date strings directly in SQLite format 'YYYY-MM-DD'
    trends = db.query(
        func.date(Deployment.timestamp).label("date"),
        func.avg(Deployment.risk_score).label("avg_risk")
    ).filter(
        Deployment.timestamp >= window_start,
        Deployment.risk_score.isnot(None)
    ).group_by(
        func.date(Deployment.timestamp)
    ).order_by(
        func.date(Deployment.timestamp).asc()
    ).all()
    
    return [
        {
            "date": t.date,
            "average_risk": round(t.avg_risk, 2)
        }
        for t in trends
    ]


def calculate_incident_frequency(db: Session, window_hours: int = 168) -> int:
    window_start = get_window_start(window_hours)
    return db.query(Deployment).filter(
        Deployment.timestamp >= window_start,
        Deployment.incident_flag == True
    ).count()


def generate_health_index(db: Session, window_hours: int = 168) -> Dict[str, Any]:
    success_rate = calculate_success_rate(db, window_hours)
    stability = compute_service_stability(db, service=None, window_hours=window_hours)
    incident_count = calculate_incident_frequency(db, window_hours)
    
    # A composite score logic
    # Start with average of success and stability
    base_health = (success_rate + stability) / 2
    
    # Penalty for total incidents (capped)
    incident_penalty = min(incident_count * 2, 20)
    health_index = max(0.0, base_health - incident_penalty)
    
    return {
        "health_index": round(health_index, 2),
        "success_rate": success_rate,
        "global_stability": stability,
        "incident_frequency": incident_count,
        "time_window_hours": window_hours
    }
