import sys
import os
import argparse
import random
import time
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add the project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.app.models.deployment import Deployment, Base
from backend.app.schemas.analysis_schema import AnalysisRequest
from backend.app.services.analysis_orchestrator import evaluate_deployment, register_deployment_outcome

def setup_db(use_prod):
    if use_prod:
        from backend.app.database import SessionLocal
        return SessionLocal()
    
    # Use in-memory or separate file SQLite for pure testing
    engine = create_engine("sqlite:///./test_simulation.db", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return Session()

def run_simulation(args):
    db = setup_db(args.use_prod_db)
    print(f"Starting AEGIS CI/CD Simulation...")
    print(f"Scenario: {args.scenario}")
    print(f"Count: {args.count}")
    print(f"Target DB: {'Production' if args.use_prod_db else 'Test Database'}")
    
    # Base repos
    repos = ["frontend-app", "payment-service", "auth-gateway"]

    # Simple background task mock
    class MockBackgroundTasks:
        def add_task(self, func, *args, **kwargs):
            # Synchronously execute for simulation to update DB immediately
            func(*args, **kwargs)

    bg_tasks = MockBackgroundTasks()
    
    stats = {"ALLOW": 0, "WARN": 0, "BLOCK": 0}

    try:
        for i in range(args.count):
            repo = random.choice(repos)
            
            # Feature logic based on scenario
            coverage = 85
            churn = 100
            complexity = 15
            
            if args.scenario == "healthy":
                coverage = random.randint(80, 95)
                churn = random.randint(50, 200)
            elif args.scenario == "degrading":
                coverage = random.randint(60, 80)
                churn = random.randint(300, 600)
                complexity = random.randint(20, 40)
            elif args.scenario == "crisis":
                # Spikes!
                if i % 3 == 0:
                    churn = random.randint(1000, 2000)
                    coverage = random.randint(40, 60)
                else:
                    churn = random.randint(800, 1500)
            
            req = AnalysisRequest(
                repo_name=repo,
                commit_hash=f"sim_{args.scenario}_{i}",
                author=f"sim_user_{i % 5}",
                files_changed=random.randint(1, 10),  
                dependency_updates=random.randint(0, 5),  
                historical_failures=random.randint(0, 3), 
                deployment_frequency=random.randint(1, 10),
                commit_count=random.randint(1, 20),
                test_coverage=coverage,
                code_churn=churn,
                cyclomatic_complexity=complexity,
                critical_issues=1 if args.scenario == "crisis" else 0
            )
            
            print(f"\nSimulating Deploy {i+1}/{args.count}: {repo}")
            
            # Evaluate
            try:
                result = evaluate_deployment(req, db, bg_tasks)
                
                if result.risk_level == "LOW":
                    decision = "ALLOW"
                elif result.risk_level == "MEDIUM":
                    decision = "WARN"
                else:
                    decision = "BLOCK"
                    
                stats[decision] += 1
                
                print(f"Decision: {decision}")
                print(f"Risk Score: {result.risk_score}")
                print(f"Risk Level: {result.risk_level}")
                
                # Feedback loop failure injection
                is_failure = random.random() < args.inject_failure_rate
                if args.scenario == "crisis" and decision == "ALLOW":
                    is_failure = True # Force failures if we erroneously allow a crisis
                    
                print(f"Simulated Actual Failure: {is_failure}")
                
                # Find the deployment ID just created
                dep = db.query(Deployment).order_by(Deployment.id.desc()).first()
                if dep:
                    outcome = "failure" if is_failure else "success"
                    register_deployment_outcome(db, dep.id, outcome)
                    db.commit()
                    print(f"Registered feedback.")
                    
            except Exception as e:
                print(f"Simulation error: {e}")
                
            time.sleep(0.1) # small pause
            
    finally:
        db.close()
        
    print("\n--- Simulation Complete ---")
    print("Decision Stats:", stats)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AEGIS CI/CD Deployment Simulator")
    parser.add_argument("--scenario", type=str, choices=["healthy", "degrading", "crisis"], default="healthy")
    parser.add_argument("--count", type=int, default=10)
    parser.add_argument("--inject-failure-rate", type=float, default=0.1)
    parser.add_argument("--use-prod-db", action="store_true", help="Use the production database instead of test sqlite db")
    parser.add_argument("--seed", type=int, help="Random seed for reproducibility")
    
    args = parser.parse_args()
    if args.seed is not None:
        random.seed(args.seed)
        
    run_simulation(args)
