import asyncio
import os
import glob
import json
from pprint import pprint
from app.database import SessionLocal, Base, engine
from app.models.deployment import Deployment
from app.schemas.analysis_schema import AnalysisRequest
from app.services.ml_engine import ml_engine
from app.services.analysis_orchestrator import evaluate_deployment, register_deployment_outcome
from app.services.analytics_engine import get_ml_performance_metrics

from fastapi import BackgroundTasks
bg = BackgroundTasks()

db = SessionLocal()

def verify_intelligence():
    print("--- 1. Resetting Data and Seeding 35 Historical ---")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    for i in range(1, 36):
        # 15 successful deployments, 20 failed
        outcome = "success" if i <= 15 else "failure"
        commit_c = 2 if i <= 15 else 40
        dep = Deployment(
            repo_name="auth-service",
            commit_count=commit_c,
            files_changed=2 if i <= 15 else 20,
            code_churn=50 if i <= 15 else 800,
            test_coverage=95.0 if i <= 15 else 40.0,
            deployment_outcome=outcome,
            sensitive_files='["auth"]' if i > 15 else '[]'
        )
        db.add(dep)
    db.commit()
    print("Database seeding successful. Current records:", db.query(Deployment).count())

    print("\n--- 2. Training ML Model via service ---")
    result = ml_engine.train_model(db)
    print("Training Result:", result)
    
    # Metadata verify
    latest_meta = glob.glob(os.path.join(os.path.dirname(__file__), "app", "ml", "models", "*.meta.json"))
    if latest_meta:
        latest_meta.sort(reverse=True)
        with open(latest_meta[0], "r") as f:
            print("Generated Metadata JSON:", json.load(f))

    print("\n--- 3. Testing Intelligence Pipeline Inference ---")
    req = AnalysisRequest(
        repo_name="auth-service",
        commit_count=180, # Very high! Huge Drift.
        files_changed=45,
        code_churn=1500,
        test_coverage=30.0,
        dependency_updates=5,
        historical_failures=10,
        deployment_frequency=2,
        pipeline_source="github",
        branch_name="feature/auth-bypass"
    )
    
    response = evaluate_deployment(req, db, bg)
    print("\nAnalysis Response Details:")
    print("Deployment ID:", response.deployment_id)
    print("Risk Score:", response.risk_score)
    print("Risk Level:", response.risk_level)
    print("Risk Factors Explained:")
    for rf in response.risk_factors:
        print(f" - {rf}")

    print("\n--- 4. Checking Deployment Storage Context ---")
    dep = db.query(Deployment).filter(Deployment.id == response.deployment_id).first()
    print("Feature Signature Hash:", dep.feature_signature)
    print("Drift Detected:", dep.drift_detected)
    print("Drift Score:", dep.drift_score)
    print("Prediction Confidence:", dep.prediction_confidence_score)

    print("\n--- 5. Testing Feedback Loop Integration ---")
    # Simulate CI/CD finishing the deployment with failure
    register_deployment_outcome(db, response.deployment_id, "failure")
    db.refresh(dep)
    
    print("Post-Feedback Loop Database State:")
    print("Predicted Failure:", dep.predicted_failure)
    print("Actual Outcome (Failed):", dep.actual_outcome)
    print("Prediction Correct:", dep.prediction_correct)
    
    print("\n--- 6. Telemetry Intelligence ---")
    metrics = get_ml_performance_metrics(db, limit=50)
    print("Precision & Recall Metrics:", metrics)

verify_intelligence()
