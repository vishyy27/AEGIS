from fastapi import APIRouter

# from sqlalchemy.orm import Session
# from ..database import get_db
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..database import get_db
from ..models.deployment import Deployment

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
