from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..database import get_db
from ..models.deployment import Deployment
from ..services.analytics_engine import generate_health_index, get_all_services_stability, detect_risk_trends

router = APIRouter(prefix="/api/insights", tags=["insights"])


@router.get("/")
def get_insights(db: Session = Depends(get_db)):
    deployments = db.query(Deployment).all()
    if not deployments:
        return {
            "average_risk": 0,
            "highest_risk_service": "None",
            "most_common_risk_factor": "None",
        }

    average_risk = sum(d.risk_score for d in deployments) / len(deployments)
    highest_risk_service = max(deployments, key=lambda d: d.risk_score).repo_name

    # Compute most common risk factor implicitly since not direct string array in DB
    issues = {
        "High code churn": sum(
            1 for d in deployments if d.code_churn and d.code_churn > 500
        ),
        "Low test coverage": sum(
            1 for d in deployments if d.test_coverage and d.test_coverage < 70
        ),
        "Frequent historical failures": sum(
            1
            for d in deployments
            if d.historical_failures and d.historical_failures > 3
        ),
    }
    most_common_risk_factor = (
        max(issues.items(), key=lambda x: x[1])[0]
        if max(issues.values()) > 0
        else "None"
    )

    return {
        "average_risk": round(average_risk, 2),
        "highest_risk_service": highest_risk_service or "Unknown",
        "most_common_risk_factor": most_common_risk_factor,
    }

@router.get("/deployment-health")
def get_deployment_health(
    time_window: int = Query(168, description="Time window in hours"),
    db: Session = Depends(get_db)
):
    return generate_health_index(db, window_hours=time_window)

@router.get("/service-stability")
def get_service_stability(
    time_window: int = Query(168, description="Time window in hours"),
    db: Session = Depends(get_db)
):
    return get_all_services_stability(db, window_hours=time_window)

@router.get("/risk-trends")
def get_risk_trends(
    time_window: int = Query(720, description="Time window in hours"),
    db: Session = Depends(get_db)
):
    return detect_risk_trends(db, window_hours=time_window)
