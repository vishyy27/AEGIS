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


def get_rolling_failure_rate(db: Session, repo_name: str, limit: int = 10) -> float:
    recent = db.query(Deployment).filter(
        Deployment.repo_name == repo_name,
        Deployment.deployment_outcome.isnot(None)
    ).order_by(Deployment.timestamp.desc()).limit(limit).all()
    
    if not recent:
        return 0.0
        
    failures = sum(1 for d in recent if d.deployment_outcome in ["failure", "error", "rollback", "failed"])
    return round((failures / len(recent)) * 100.0, 2)


def get_rolling_avg_risk(db: Session, repo_name: str, limit: int = 5) -> float:
    recent = db.query(Deployment.risk_score).filter(
        Deployment.repo_name == repo_name,
        Deployment.risk_score.isnot(None)
    ).order_by(Deployment.timestamp.desc()).limit(limit).all()
    
    if not recent:
        return 0.0
        
    total = sum(r[0] for r in recent)
    return round(total / len(recent), 2)


def get_ml_performance_metrics(db: Session, limit: int = 50) -> Dict[str, Any]:
    recent = db.query(Deployment).filter(
        Deployment.ml_used == True,
        Deployment.deployment_outcome.isnot(None),
        Deployment.ml_prediction_prob.isnot(None)
    ).order_by(Deployment.timestamp.desc()).limit(limit).all()
    
    if not recent:
        return {"status": "insufficient_data", "samples": 0}
        
    correct_predictions = 0
    true_failures = 0
    predicted_failures = 0
    true_positive_failures = 0
    
    for d in recent:
        actual_failure = d.deployment_outcome in ["failure", "error", "rollback", "failed"]
        predicted_failure = d.ml_prediction_prob >= 0.5
        
        if actual_failure == predicted_failure:
            correct_predictions += 1
            
        if actual_failure:
            true_failures += 1
        if predicted_failure:
            predicted_failures += 1
            if actual_failure:
                true_positive_failures += 1
                
    accuracy = (correct_predictions / len(recent)) * 100.0
    precision = (true_positive_failures / predicted_failures * 100.0) if predicted_failures > 0 else 0.0
    
    return {
        "status": "ready",
        "samples": len(recent),
        "rolling_accuracy": round(accuracy, 2),
        "failure_prediction_precision": round(precision, 2),
        "model_versions_in_window": list(set(d.model_version for d in recent if d.model_version))
    }
