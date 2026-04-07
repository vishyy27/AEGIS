from app.schemas.analysis_schema import AnalysisRequest
from app.services.analysis_orchestrator import evaluate_deployment
from app.database import SessionLocal
import traceback

def test():
    req = AnalysisRequest(
        repo_name="user-service",
        commit_count=12,
        files_changed=5,
        code_churn=350,
        test_coverage=70,
        dependency_updates=3,
        historical_failures=4,
        deployment_frequency=3,
        changed_files=["src/auth.py", "tests/demo.py"]
    )
    db = SessionLocal()
    try:
        res = evaluate_deployment(req, db)
        with open("utf8_out.txt", "w", encoding="utf-8") as f:
            f.write("Success")
    except Exception as e:
        with open("utf8_out.txt", "w", encoding="utf-8") as f:
            f.write(traceback.format_exc())

test()

