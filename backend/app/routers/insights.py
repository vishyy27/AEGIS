from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from ..database import get_db
from ..models.deployment import Deployment
from ..services.analytics_engine import generate_health_index, get_all_services_stability, detect_risk_trends

router = APIRouter(prefix="/api/insights", tags=["insights"])


@router.get("/")
def get_insights(db: Session = Depends(get_db)):
    stats = db.query(
        func.avg(Deployment.risk_score).label("average_risk"),
        func.sum(case((Deployment.code_churn > 500, 1), else_=0)).label("high_code_churn"),
        func.sum(case((Deployment.test_coverage < 70, 1), else_=0)).label("low_test_coverage"),
        func.sum(case((Deployment.historical_failures > 3, 1), else_=0)).label("frequent_failures"),
        func.count(Deployment.id).label("total")
    ).one_or_none()

    if not stats or not stats.total or stats.total == 0:
        return {
            "average_risk": 0,
            "highest_risk_service": "None",
            "most_common_risk_factor": "None",
        }

    average_risk = stats.average_risk or 0

    highest_risk_service_row = db.query(Deployment.repo_name).order_by(Deployment.risk_score.desc()).first()
    highest_risk_service = highest_risk_service_row[0] if highest_risk_service_row else "Unknown"

    issues = {
        "High code churn": stats.high_code_churn or 0,
        "Low test coverage": stats.low_test_coverage or 0,
        "Frequent historical failures": stats.frequent_failures or 0,
    }
    
    most_common_risk_factor = (
        max(issues.items(), key=lambda x: x[1])[0]
        if max(issues.values()) > 0
        else "None"
    )

    return {
        "average_risk": round(average_risk, 2),
        "highest_risk_service": highest_risk_service,
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
