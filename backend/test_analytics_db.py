import sys
sys.path.append(".")

from app.database import SessionLocal, engine, Base
from app.models.deployment import Deployment
from datetime import datetime, timedelta
import random

Base.metadata.create_all(bind=engine)
db = SessionLocal()

services = ["auth-service", "payment-service", "billing-service", "user-service"]
now = datetime.utcnow()

print("Inserting test data...")
try:
    for i in range(20):
        d = Deployment(
            service=random.choice(services),
            repo_name=random.choice(services),
            environment="production",
            risk_score=random.uniform(10.0, 95.0),
            status=random.choice(["success", "success", "success", "failure"]),
            deployment_outcome=random.choice(["success", "success", "success", "failure"]),
            incident_flag=random.choice([True, False, False, False]),
            code_churn=random.randint(100, 1000),
            test_coverage=random.uniform(50.0, 99.0),
            historical_failures=random.randint(0, 5),
            timestamp=now - timedelta(hours=random.randint(1, 700))
        )
        db.add(d)
    db.commit()
    print("Database seeding successful.")
except Exception as e:
    db.rollback()
    print("Seeding error:", e)

from app.services.analytics_engine import generate_health_index, get_all_services_stability, detect_risk_trends

print("\n--- Analytics Engine Function Tests ---")
print("Health Index:", generate_health_index(db))
print("Service Stability:", get_all_services_stability(db))
print("Risk Trends:", detect_risk_trends(db)[:3])

print("\n--- API Endpoint Tests ---")
from app.routers.dashboard import get_dashboard_summary
from app.routers.insights import get_insights, get_deployment_health

from app.routers.deployments import list_deployments
from app.routers.alerts import get_alerts

try:
    print("\nTesting /api/dashboard/summary...")
    dash_sum = get_dashboard_summary(db)
    print("Dashboard keys:", list(dash_sum.keys()))
    print("Global Risk Score:", dash_sum['globalRiskScore'])

    print("\nTesting /api/insights...")
    ins_sum = get_insights(db)
    print("Insights Data:", ins_sum)

    print("\nTesting /api/insights/deployment-health...")
    health = get_deployment_health(168, db)
    print("Health:", health)

    print("\nTesting backwards compatibility: /api/deployments...")
    # list_deployments(skip=0, limit=100, db)
    deps = list_deployments(0, 100, db)
    print(f"Total deployments listed: {len(deps)}")

    print("\nTesting backwards compatibility: /api/alerts...")
    # get_alerts(db)
    alts = get_alerts(db)
    print(f"Total alerts listed: {len(alts)}")

except Exception as e:
    import traceback
    traceback.print_exc()

db.close()
print("Tests completed successfully.")
