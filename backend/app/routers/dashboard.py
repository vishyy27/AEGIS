from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from ..database import get_db

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/summary")
def get_dashboard_summary(db: Session = Depends(get_db)):
    try:
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
                "deploymentHealthIndex": health_data.get("health_index", 100),
                "serviceStabilityScore": health_data.get("global_stability", 100),
                "incidentFrequency": health_data.get("incident_frequency", 0),
                "advancedRiskTrends": advanced_trends or []
            }

        global_risk_score = stats.global_risk_score or 0
        success_rate = health_data.get("success_rate", 100)

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

        response = {
            "globalRiskScore": round(global_risk_score, 2),
            "successRate": round(success_rate, 2),
            "riskTrend": risk_trend,
            "topRiskFactors": top_risk_factors,
            
            # Phase 7 new metrics
            "deploymentHealthIndex": health_data.get("health_index", 100),
            "serviceStabilityScore": health_data.get("global_stability", 100),
            "incidentFrequency": health_data.get("incident_frequency", 0),
            "advancedRiskTrends": advanced_trends or []
        }

        print(f"[DEBUG] Number of deployments fetched: {stats.total if stats else 0}")
        print(f"[DEBUG] Metrics returned: {response}")

        return response
    except Exception as e:
        print(f"Error in /api/dashboard/summary: {e}")
        import traceback
        traceback.print_exc()
        return {
            "globalRiskScore": 0,
            "successRate": 0,
            "riskTrend": [],
            "topRiskFactors": [],
            "deploymentHealthIndex": 0,
            "serviceStabilityScore": 0,
            "incidentFrequency": 0,
            "advancedRiskTrends": []
        }
