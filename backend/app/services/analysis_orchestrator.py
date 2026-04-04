import json
from sqlalchemy.orm import Session
from ..models.deployment import Deployment
from ..schemas.analysis_schema import AnalysisRequest, AnalysisResponse
from .risk_engine import calculate_risk_score
import sys
# need to handle recommendation_engine, wait it's in recommendation_engine
from .recommendation_engine import generate_recommendations
from .alert_service import check_and_create_alert
from .change_intelligence import analyze_code_changes

def evaluate_deployment(request: AnalysisRequest, db: Session) -> AnalysisResponse:
    # Phase 3: Pre-processing Intelligence
    intelligence = analyze_code_changes(request.dict())

    # Phase 2: Deployment Risk Score calculation
    deploy_risk_score, deploy_risk_level, deploy_risk_factors = calculate_risk_score(
        request.dict()
    )

    # Aggregation
    final_risk_score = round(
        min(0.7 * deploy_risk_score + 0.3 * intelligence["change_risk_score"], 100.0), 2
    )

    if final_risk_score >= 70.0:
        final_risk_level = "HIGH"
    elif final_risk_score >= 40.0:
        final_risk_level = "MEDIUM"
    else:
        final_risk_level = "LOW"

    combined_risk_factors = deploy_risk_factors + intelligence["risk_categories"]

    # Generate recommendations based on combined risk factors
    recommendations = generate_recommendations(combined_risk_factors)

    # Store deployment in DB
    deployment = Deployment(
        repo_name=request.repo_name,
        commit_count=request.commit_count,
        files_changed=request.files_changed,
        code_churn=request.code_churn,
        test_coverage=request.test_coverage,
        dependency_updates=request.dependency_updates,
        historical_failures=request.historical_failures,
        deployment_frequency=request.deployment_frequency,
        risk_score=final_risk_score,
        risk_level=final_risk_level,
        change_risk_score=intelligence["change_risk_score"],
        risk_categories=json.dumps(intelligence["risk_categories"]),
        sensitive_files=json.dumps(intelligence["sensitive_files"]),
        churn_ratio=intelligence["churn_ratio"],
        commit_density=intelligence["commit_density"],
        pipeline_source=request.pipeline_source,
        branch_name=request.branch_name,
        commit_hash=request.commit_hash,
        deployment_environment=request.deployment_environment,
    )
    db.add(deployment)
    db.commit()
    db.refresh(deployment)

    # Check and generate alerts using final aggregated risk score
    check_and_create_alert(
        db, deployment.id, final_risk_score, request.historical_failures
    )

    return AnalysisResponse(
        deployment_id=deployment.id,
        risk_score=final_risk_score,
        risk_level=final_risk_level,
        risk_factors=combined_risk_factors,
        recommendations=recommendations,
    )
