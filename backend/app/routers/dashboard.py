from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/summary")
def get_dashboard_summary(db: Session = Depends(get_db)):

    from ..models.deployment import Deployment
    from sqlalchemy import func

    # Query metrics
    deployments = db.query(Deployment).all()
    if not deployments:
        return {
            "globalRiskScore": 0,
            "successRate": 100,
            "riskTrend": [],
            "topRiskFactors": [],
        }

    global_risk_score = sum(d.risk_score for d in deployments) / len(deployments)

    # Calculate success rate as deployments not marked HIGH risk, or just by some logic
    success_count = sum(1 for d in deployments if d.risk_level != "HIGH")
    success_rate = (success_count / len(deployments)) * 100

    # Trend of last 5
    recent = sorted(deployments, key=lambda d: d.timestamp, reverse=True)[:5]
    risk_trend = [d.risk_score for d in reversed(recent)]

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
    }
