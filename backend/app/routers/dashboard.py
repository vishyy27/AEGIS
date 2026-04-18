from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from ..database import get_db

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/summary")
def get_dashboard_summary(db: Session = Depends(get_db)):

    from ..models.deployment import Deployment
    from ..services.analytics_engine import generate_health_index, get_all_services_stability, detect_risk_trends

    health_data = generate_health_index(db, window_hours=720) # 30 days
    stability_data = get_all_services_stability(db, window_hours=720)
    advanced_trends = detect_risk_trends(db, window_hours=720)
    
    stats = db.query(
        func.avg(Deployment.risk_score).label("global_risk_score"),
        func.sum(case((Deployment.code_churn > 500, 1), else_=0)).label("high_code_churn"),
        func.sum(case((Deployment.test_coverage < 70, 1), else_=0)).label("low_test_coverage"),
        func.sum(case((Deployment.historical_failures > 3, 1), else_=0)).label("frequent_failures"),
        func.count(Deployment.id).label("total")
    ).one_or_none()
    
    if not stats or not stats.total or stats.total == 0:
        return {
            "globalRiskScore": 0,
            "successRate": 100,
            "riskTrend": [],
            "topRiskFactors": [],
            "deploymentHealthIndex": health_data["health_index"],
            "serviceStabilityScore": health_data["global_stability"],
            "incidentFrequency": health_data["incident_frequency"],
            "advancedRiskTrends": advanced_trends
        }

    global_risk_score = stats.global_risk_score or 0

    success_rate = health_data["success_rate"]

    # Trend of last 5 for backward compatibility
    recent = db.query(Deployment.risk_score).order_by(Deployment.timestamp.desc()).limit(5).all()
    risk_trend = [r[0] for r in reversed(recent) if r[0] is not None]

    # Compute risk factors from db fields
    issues = {
        "High Code Churn": stats.high_code_churn or 0,
        "Low Test Coverage": stats.low_test_coverage or 0,
        "Frequent Failures": stats.frequent_failures or 0,
    }

    # Get top 2 factors with their counts formatted as impact
    top_issues = sorted(issues.items(), key=lambda item: item[1], reverse=True)[:2]
    top_risk_factors = [
        {"factor": k, "impact": f"+{v} cases"} for k, v in top_issues if v > 0
    ]

    return {
        "globalRiskScore": round(global_risk_score, 2),
        "successRate": round(success_rate, 2),
        "riskTrend": risk_trend,
        "topRiskFactors": top_risk_factors,
        
        # Phase 7 new metrics
        "deploymentHealthIndex": health_data["health_index"],
        "serviceStabilityScore": health_data["global_stability"],
        "incidentFrequency": health_data["incident_frequency"],
        "advancedRiskTrends": advanced_trends
    }
