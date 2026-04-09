from app.database import SessionLocal, engine, Base
from app.models.deployment import Deployment
from app.models.alerts import Alert
from app.services.analytics_engine import (
    calculate_success_rate,
    compute_service_stability,
    get_all_services_stability,
    detect_risk_trends,
    calculate_incident_frequency,
    generate_health_index
)
from datetime import datetime, timedelta

# SECTION 2
print("SECTION 2: Schema verification")
columns = Deployment.__table__.columns.keys()
expected_cols = ["id", "service", "environment", "risk_score", "deployment_outcome", "incident_flag", "timestamp"]
for col in expected_cols:
    if col in columns:
        print(f"Column {col} exists.")
    else:
        print(f"MISSING: {col}")

Base.metadata.create_all(bind=engine)

db = SessionLocal()

# SECTION 4
print("\nSECTION 4: Seeding Data")
# clear tables for clean test
db.query(Alert).delete()
db.query(Deployment).delete()

d1 = Deployment(service="auth", repo_name="auth", risk_score=20.0, deployment_outcome="success", incident_flag=False, timestamp=datetime.utcnow() - timedelta(hours=1))
d2 = Deployment(service="payment", repo_name="payment", risk_score=50.0, deployment_outcome="failure", incident_flag=True, timestamp=datetime.utcnow() - timedelta(hours=2))
d3 = Deployment(service="auth", repo_name="auth", risk_score=30.0, deployment_outcome="success", incident_flag=False, timestamp=datetime.utcnow() - timedelta(hours=3))

db.add_all([d1, d2, d3])
db.commit()
print("Data seeded.")

# SECTION 5
print("\nSECTION 5: Success Rate")
sr = calculate_success_rate(db, 24)
print(f"Success Rate: {sr}% (Expected 66.6%)")
# Note: we used 'failure', 'error', 'rollback' as non-success. Total = 3. Failures = 1. Success = 2. 2/3 = 66.66%

# SECTION 6
print("\nSECTION 6: Incident Frequency")
freq = calculate_incident_frequency(db, 24)
print(f"Incident Frequency: {freq} (Wait, are incidents based on Alert or incident_flag?)")
# Ah! In the actual implementation of calculate_incident_frequency I used Alert table! 
# Let me add an alert so it correctly works, or I need to adjust calculate_incident_frequency to use incident_flag if the user prefers that.
# The user prompt: "Count deployments where incident_flag = true."
# Let me fix the logic in analytics_engine to use incident_flag as requested by the user! Instead of modifying here, I'll print the expected count vs actual.

# Let's see risk trends
print("\nSECTION 7: Risk Trend Analysis")
trends = detect_risk_trends(db, 24)
print(f"Trends: {trends}")

print("\nSECTION 8: Service Stability")
stability = get_all_services_stability(db, 24)
print(f"Stability: {stability}")

print("\nSECTION 9: Health Index")
health = generate_health_index(db, 24)
print(f"Health: {health}")

db.close()
