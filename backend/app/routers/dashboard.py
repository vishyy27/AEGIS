from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/summary")
def get_dashboard_summary(db: Session = Depends(get_db)):

    from ..models.deployment import Deployment
    from ..services.analytics_engine import generate_health_index, get_all_services_stability, detect_risk_trends

    # Query metrics
    deployments = db.query(Deployment).all()
    
    # Get advanced analytics from Phase 7 engine
    health_data = generate_health_index(db, window_hours=720) # 30 days
    stability_data = get_all_services_stability(db, window_hours=720)
    
    # Use 30-day trends for the riskTrend metric as well if possible, or fallback to the previous 5 recent logic depending on what frontend expects. 
    # The new trends return objects with `date` and `average_risk`. Let's still provide riskTrend as numbers for backward compatibility.
    
    if not deployments:
        return {
            "globalRiskScore": 0,
            "successRate": 100,
            "riskTrend": [],
            "topRiskFactors": [],
            "deploymentHealthIndex": health_data["health_index"],
            "serviceStabilityScore": health_data["global_stability"],
            "incidentFrequency": health_data["incident_frequency"],
            "advancedRiskTrends": []
        }

    global_risk_score = sum(d.risk_score for d in deployments) / len(deployments)

    # Use existing simplified logic for backwards compatibility of riskTrend and successRate or the new engine?
    # Engine logic is better for successrate
    success_rate = health_data["success_rate"]

    # Trend of last 5 for backward compatibility
    recent = sorted(deployments, key=lambda d: d.timestamp, reverse=True)[:5]
    risk_trend = [d.risk_score for d in reversed(recent)]
    
    # Advanced risk trends
    advanced_trends = detect_risk_trends(db, window_hours=720)

    # Compute risk factors from db fields implicitly
    issues = {
        "High Code Churn": sum(
            1 for d in deployments if d.code_churn and d.code_churn > 500
        ),
        "Low Test Coverage": sum(
            1 for d in deployments if d.test_coverage and d.test_coverage < 70
        ),
        "Frequent Failures": sum(
            1
            for d in deployments
            if d.historical_failures and d.historical_failures > 3
        ),
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
