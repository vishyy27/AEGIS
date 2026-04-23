import sys
sys.path.append(".")

from app.database import SessionLocal, engine, Base
from app.models.deployment import Deployment
from datetime import datetime, timedelta
import random

Base.metadata.create_all(bind=engine)
db = SessionLocal()

print("--- 1. Seeding data for ML Training ---")
services = ["ml-service", "auth-service", "billing-service", "app-service"]
now = datetime.utcnow()

try:
    for i in range(50):
        # We need a mix of successes and failures to train the model
        outcome = random.choice(["success", "success", "failure"])
        is_failure = outcome == "failure"
        
        d = Deployment(
            service=random.choice(services),
            repo_name=random.choice(services),
            environment="production",
            risk_score=random.uniform(70.0, 95.0) if is_failure else random.uniform(10.0, 40.0),
            status=outcome,
            deployment_outcome=outcome,
            incident_flag=is_failure,
            code_churn=random.randint(500, 1500) if is_failure else random.randint(10, 200),
            test_coverage=random.uniform(20.0, 60.0) if is_failure else random.uniform(80.0, 99.0),
            historical_failures=random.randint(2, 5) if is_failure else random.randint(0, 1),
            timestamp=now - timedelta(hours=random.randint(1, 700))
        )
        db.add(d)
    db.commit()
    print("Database seeding successful.")
except Exception as e:
    db.rollback()
    print("Seeding error:", e)

print("\n--- 2. Training ML Model via service ---")
from app.services.ml_engine import ml_engine

train_result = ml_engine.train_model(db)
print("Training Result:", train_result)

from app.routers.analysis import analyze_deployment
from app.schemas.analysis_schema import AnalysisRequest
import asyncio

print("\n--- 3. Testing /api/analysis/analyze with ML Engine ---")
req = AnalysisRequest(
    repo_name="auth-service",
    commit_count=10,
    files_changed=5,
    code_churn=800, # High churn -> Should hint at failure
    test_coverage=40.0, # Low coverage -> Should hint at failure
    dependency_updates=1,
    historical_failures=4, # History of failures
    deployment_frequency=12
)

async def test_analysis():
    response = await analyze_deployment(req, db)
    print("Analysis Response output:")
    print("Deployment ID:", response.deployment_id)
    print("Risk Score (should be high):", response.risk_score)
    print("Risk Level:", response.risk_level)
    print("Risk Factors:", response.risk_factors)
    
    # Check Database if ml tracks were set correctly
    dep = db.query(Deployment).filter(Deployment.id == response.deployment_id).first()
    print("\nDatabase Tracking:")
    print("ML Used:", dep.ml_used)
    print("ML Prediction Prob:", dep.ml_prediction_prob)

asyncio.run(test_analysis())

db.close()
print("Tests completed successfully.")
