from typing import Dict, Any, List
from ..models.recommendation import Recommendation


MAX_RECOMMENDATIONS = 5

def build_recommendation_context(
    request_data: Dict[str, Any],
    intelligence: Dict[str, Any],
    risk_score: float,
    deployment_history: List[Any],
    alert_history: List[Any]
) -> Dict[str, Any]:
    context = {
        "risk_score": risk_score,
        "churn_ratio": intelligence.get("churn_ratio", 0.0),
        "code_churn": request_data.get("code_churn", 0),
        "test_coverage": request_data.get("test_coverage", 100.0),
        "critical_modules": intelligence.get("sensitive_files", []),
        "past_failures": request_data.get("historical_failures", 0),
        "deployment_frequency": request_data.get("deployment_frequency", 0),
        "alert_spike": False
    }

    if alert_history and len(alert_history) > 3:
        context["alert_spike"] = True

    return context


def detect_testing_risks(context: Dict[str, Any]) -> List[Recommendation]:
    recs = []
    if context["test_coverage"] < 80:
        recs.append(
            Recommendation(
                message="Increase test coverage. Deployment contains high churn with low automated coverage.",
                category="Testing Improvements",
                priority="MEDIUM"  # baseline
            )
        )
    return recs


def detect_code_quality_risks(context: Dict[str, Any]) -> List[Recommendation]:
    recs = []
    if context["churn_ratio"] > 0.8:
        recs.append(
            Recommendation(
                message="High deletion ratio detected. Ensure architectural modifications are documented and reviewed.",
                category="Code Quality",
                priority="MEDIUM"
            )
        )
    if context["code_churn"] > 300:
        recs.append(
            Recommendation(
                message="Significant code churn detected. Consider splitting deployment due to high commit density.",
                category="Code Quality",
                priority="MEDIUM"
            )
        )
    return recs


def detect_deployment_strategy_risks(context: Dict[str, Any]) -> List[Recommendation]:
    recs = []
    if context["past_failures"] > 2:
        recs.append(
            Recommendation(
                message="Frequent historical failures on this service. Consider canary deployments or extended QA.",
                category="Deployment Strategy",
                priority="HIGH"
            )
        )
    return recs


def detect_infrastructure_risks(context: Dict[str, Any]) -> List[Recommendation]:
    recs = []
    if context.get("critical_modules"):
        for mod in context["critical_modules"]:
            recs.append(
                Recommendation(
                    message=f"Critical infrastructure/security module '{mod}' modified. Ensure strict peer review.",
                    category="Infrastructure Safety",
                    priority="HIGH",
                    affected_module=mod
                )
            )
    return recs


def detect_rollback_risks(context: Dict[str, Any]) -> List[Recommendation]:
    recs = []
    if context["deployment_frequency"] < 5 and context["risk_score"] > 60:
        recs.append(
            Recommendation(
                message="Low deployment frequency with high risk score. Ensure rollback automated scripts are verified.",
                category="Rollback Preparedness",
                priority="HIGH"
            )
        )
    if context["alert_spike"]:
        recs.append(
            Recommendation(
                message="Recent alert spike detected in this service's environment. Ensure rollback readiness.",
                category="Rollback Preparedness",
                priority="HIGH"
            )
        )
    return recs


def calculate_recommendation_priority(rec: Recommendation, context: Dict[str, Any]):
    # Dynamic Priority Scoring Engine
    score = context.get("risk_score", 0)
    
    if score > 90 and context.get("critical_modules"):
        rec.priority = "CRITICAL"
    elif score > 80:
        if rec.priority != "CRITICAL":
            rec.priority = "HIGH"
    elif context.get("test_coverage", 100) < 60 and context.get("code_churn", 0) > 200:
        if rec.priority not in ["CRITICAL", "HIGH"]:
            rec.priority = "HIGH"
    elif context.get("past_failures", 0) > 3:
        rec.priority = "CRITICAL"


def generate_context_recommendations(context: Dict[str, Any]) -> List[Recommendation]:
    candidates = []
    candidates.extend(detect_testing_risks(context))
    candidates.extend(detect_code_quality_risks(context))
    candidates.extend(detect_deployment_strategy_risks(context))
    candidates.extend(detect_infrastructure_risks(context))
    candidates.extend(detect_rollback_risks(context))
    
    if not candidates:
        if context.get("risk_score", 0) < 40:
            candidates.append(
                Recommendation(
                    message="Safe to deploy. Continue standard monitoring.",
                    category="Code Quality",
                    priority="LOW"
                )
            )
            
    # Apply priority logic
    for rec in candidates:
        calculate_recommendation_priority(rec, context)
        rec.source_engine = "AI_RECOMMENDATION_ENGINE"
        
    priority_order = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}
    
    # Sort by descending priority
    sorted_recs = sorted(candidates, key=lambda r: priority_order.get(r.priority, 0), reverse=True)
    
    return sorted_recs[:MAX_RECOMMENDATIONS]
