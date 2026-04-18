from sqlalchemy.orm import Session
from sqlalchemy import func, case, extract, or_
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
    
    is_failure = or_(
        Deployment.status.in_(["failure", "error", "rollback"]),
        Deployment.deployment_outcome.in_(["failure", "error", "rollback"])
    )
    
    stats_query = db.query(
        func.sum(case((is_failure, 1), else_=0)).label("failures"),
        func.sum(case((Deployment.risk_score >= 70.0, 1), else_=0)).label("high_risks"),
        func.sum(case((Deployment.incident_flag == True, 1), else_=0)).label("incidents"),
        func.count(Deployment.id).label("total")
    ).filter(Deployment.timestamp >= window_start)
    
    if service:
        stats_query = stats_query.filter(Deployment.repo_name == service)
        
    stats = stats_query.one_or_none()
    
    if not stats or not stats.total or stats.total == 0:
        return 100.0
    
    failures = stats.failures or 0
    high_risks = stats.high_risks or 0
    incidents = stats.incidents or 0
        
    score = 100.0 - (failures * 10) - (high_risks * 2) - (incidents * 5)
        
    return max(0.0, round(score, 2))


def get_all_services_stability(db: Session, window_hours: int = 168) -> List[Dict[str, Any]]:
    window_start = get_window_start(window_hours)
    
    is_failure = or_(
        Deployment.status.in_(["failure", "error", "rollback"]),
        Deployment.deployment_outcome.in_(["failure", "error", "rollback"])
    )
    
    stats_query = db.query(
        Deployment.repo_name,
        func.sum(case((is_failure, 1), else_=0)).label("failures"),
        func.sum(case((Deployment.risk_score >= 70.0, 1), else_=0)).label("high_risks"),
        func.sum(case((Deployment.incident_flag == True, 1), else_=0)).label("incidents")
    ).filter(
        Deployment.timestamp >= window_start,
        Deployment.repo_name.isnot(None)
    ).group_by(Deployment.repo_name).all()
    
    results = []
    for row in stats_query:
        failures = row.failures or 0
        high_risks = row.high_risks or 0
        incidents = row.incidents or 0
        score = 100.0 - (failures * 10) - (high_risks * 2) - (incidents * 5)
        
        results.append({
            "service": row.repo_name,
            "stability_index": max(0.0, round(score, 2))
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
