import json
from fastapi import BackgroundTasks
from sqlalchemy.orm import Session
from ..models.deployment import Deployment
from ..models.alerts import Alert
from ..schemas.analysis_schema import AnalysisRequest, AnalysisResponse
from .risk_engine import calculate_risk_score
from .recommendation_engine import build_recommendation_context, generate_context_recommendations
from .alert_service import run_alert_intelligence_pipeline, analyze_deployment_history
from .change_intelligence import analyze_code_changes
from .analytics_engine import get_rolling_failure_rate, get_rolling_avg_risk
from .ml_engine import ml_engine

def evaluate_deployment(request: AnalysisRequest, db: Session, background_tasks: BackgroundTasks) -> AnalysisResponse:
    # Phase 3: Pre-processing Intelligence
    intelligence = analyze_code_changes(request.dict())

    # Phase 2: Deployment Risk Score calculation (Legacy Rule Engine Fallback)
    deploy_risk_score, deploy_risk_level, deploy_risk_factors = calculate_risk_score(
        request.dict()
    )
    
    # Phase 8.2: Context Hydration
    failure_rate_last_10 = get_rolling_failure_rate(db, request.repo_name, limit=10)
    avg_risk_last_5 = get_rolling_avg_risk(db, request.repo_name, limit=5)

    # Initialize bare Deployment for the ML Engine evaluation
    deployment = Deployment(
        repo_name=request.repo_name,
        commit_count=request.commit_count,
        files_changed=request.files_changed,
        code_churn=request.code_churn,
        test_coverage=request.test_coverage,
        dependency_updates=request.dependency_updates,
        historical_failures=request.historical_failures,
        deployment_frequency=request.deployment_frequency,
        
        # Extracted metrics
        change_risk_score=intelligence["change_risk_score"],
        risk_categories=json.dumps(intelligence["risk_categories"]),
        sensitive_files=json.dumps(intelligence["sensitive_files"]),
        churn_ratio=intelligence["churn_ratio"],
        commit_density=intelligence["commit_density"],
        
        # Hydrated context telemetry
        failure_rate_last_10=failure_rate_last_10,
        avg_risk_last_5=avg_risk_last_5,
        
        pipeline_source=request.pipeline_source,
        branch_name=request.branch_name,
        commit_hash=request.commit_hash,
        deployment_environment=request.deployment_environment
    )

    # Phase 8.2: ML Prediction and Hybrid Strategy Blend
    deployment.ml_used = False
    deployment.ml_prediction_prob = None
    deployment.model_version = None
    deployment.prediction_confidence_score = None
    
    try:
        ml_risk_score, ml_risk_level, ml_prediction_prob = ml_engine.predict_risk(deployment)
        deployment.ml_prediction_prob = ml_prediction_prob
        deployment.ml_used = True
        deployment.model_version = ml_engine.current_version
        
        confidence = abs(0.5 - ml_prediction_prob) * 2.0
        deployment.prediction_confidence_score = confidence
        
        if confidence < 0.30:
            # High uncertainty! Blend gracefully. High code churn/anomaly but strange signals.
            blended_score = (0.7 * ml_risk_score) + (0.3 * deploy_risk_score)
            deployment.risk_score = round(blended_score, 2)
            
            # Recalculate Level
            if deployment.risk_score >= 70.0:
                deployment.risk_level = "HIGH"
            elif deployment.risk_score >= 40.0:
                deployment.risk_level = "MEDIUM"
            else:
                deployment.risk_level = "LOW"
        else:
            deployment.risk_score = ml_risk_score
            deployment.risk_level = ml_risk_level
            
    except Exception as e:
        print(f"ML Prediction failed/missing: {e}. Defaulting to rule engine.")
        # Fallback 100% to rules
        deployment.risk_score = round(
            min(0.7 * deploy_risk_score + 0.3 * intelligence["change_risk_score"], 100.0), 2
        )
        if deployment.risk_score >= 70.0:
            deployment.risk_level = "HIGH"
        elif deployment.risk_score >= 40.0:
            deployment.risk_level = "MEDIUM"
        else:
            deployment.risk_level = "LOW"

    combined_risk_factors = deploy_risk_factors + intelligence["risk_categories"]

    # Persist the deployment
    db.add(deployment)
    db.commit()
    db.refresh(deployment)

    # Check for background retraining threshold
    total_deploys = db.query(Deployment).filter(Deployment.deployment_outcome.isnot(None)).count()
    if total_deploys > 0 and total_deploys % 50 == 0:
        background_tasks.add_task(ml_engine.train_model, db)

    # Run alert intelligence pipeline
    run_alert_intelligence_pipeline(db, deployment)

    # Phase 6: Recommendation Engine Context & Generation
    dep_history = analyze_deployment_history(db, request.repo_name)
    alert_history = db.query(Alert).filter(Alert.affected_service == request.repo_name).order_by(Alert.timestamp.desc()).limit(10).all()
    
    rec_context = build_recommendation_context(
        request.dict(),
        intelligence,
        deployment.risk_score,
        dep_history,
        alert_history
    )
    
    structured_recs = generate_context_recommendations(rec_context)
    
    # Persist structured recommendations
    for rec in structured_recs:
        rec.deployment_id = deployment.id
        db.add(rec)
        
    if structured_recs:
        top_rec = structured_recs[0]
        deployment.primary_recommendation_priority = top_rec.priority
        deployment.primary_recommendation_category = top_rec.category
        
    db.commit()

    legacy_recs = [r.message for r in structured_recs]
    context_recs_out = [
        {
            "message": r.message, 
            "priority": r.priority, 
            "category": r.category, 
            "affected_module": r.affected_module
        } for r in structured_recs
    ]

    return AnalysisResponse(
        deployment_id=deployment.id,
        risk_score=deployment.risk_score,
        risk_level=deployment.risk_level,
        risk_factors=combined_risk_factors,
        recommendations=legacy_recs,
        context_recommendations=context_recs_out
    )
