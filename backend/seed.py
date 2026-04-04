import os
import sys

sys.path.insert(0, os.path.abspath("."))
from app.database import engine, Base
from app.models.deployment import Deployment
from sqlalchemy.orm import Session

# Create tables based on imported models
Base.metadata.create_all(bind=engine)

# Seed a mock deployment for testing the dashboard
with Session(engine) as session:
    if not session.query(Deployment).first():
        d = Deployment(
            repo_name="aegis-test",
            commit_count=10,
            files_changed=5,
            code_churn=100,
            test_coverage=85.0,
            dependency_updates=2,
            historical_failures=1,
            deployment_frequency=5,
            risk_score=25.0,
            risk_level="LOW",
        )
        session.add(d)
        session.commit()
        print("Database initialized and mock deployment seeded.")
    else:
        print("Database already contains deployments.")
