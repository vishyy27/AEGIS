"""
Phase 11.6: Simulation Engine.
Allows synthetic deployment testing BEFORE release using real ML + Policy engines.
"""

import logging
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from ..models.deployment import Deployment
from ..models.phase11_models import SimulationRun
from ..config import settings

logger = logging.getLogger("aegis.simulation")


class SimulationEngine:
    def run_simulation(self, db: Session, params: Dict[str, Any], created_by: str = "api") -> Dict[str, Any]:
        """Run a synthetic deployment simulation using real ML and policy engines."""
        from .ml_engine import ml_engine
        from .risk_engine import calculate_risk_score
        from .policy_engine import evaluate_intelligent_policy
        from .xai_engine import xai_engine

        sim_name = params.get("simulation_name", f"sim-{datetime.utcnow().strftime('%H%M%S')}")

        # Create a transient Deployment object (NOT persisted)
        deployment = Deployment(
            repo_name=params.get("repo_name", "simulation/test-repo"),
            commit_count=params.get("commit_count", 5),
            files_changed=params.get("files_changed", 10),
            code_churn=params.get("code_churn", 200),
            test_coverage=params.get("test_coverage", 80.0),
            dependency_updates=params.get("dependency_updates", 0),
            historical_failures=params.get("historical_failures", 0),
            deployment_frequency=params.get("deployment_frequency", 3),
            churn_ratio=params.get("churn_ratio", 0.5),
            commit_density=params.get("commit_density", 2.0),
            failure_rate_last_10=params.get("failure_rate_last_10", 0.0),
            avg_risk_last_5=params.get("avg_risk_last_5", 30.0),
            has_db_migration=params.get("has_db_migration", False),
            has_auth_changes=params.get("has_auth_changes", False),
            has_payment_changes=params.get("has_payment_changes", False),
            has_core_module_changes=params.get("has_core_module_changes", False),
            sensitive_files=json.dumps(params.get("sensitive_files", [])),
        )

        # Static risk calculation
        static_score, static_level, static_factors = calculate_risk_score({
            "commit_count": deployment.commit_count,
            "files_changed": deployment.files_changed,
            "code_churn": deployment.code_churn,
            "test_coverage": deployment.test_coverage,
            "dependency_updates": deployment.dependency_updates,
            "historical_failures": deployment.historical_failures,
            "deployment_frequency": deployment.deployment_frequency,
        })

        # ML prediction
        ml_prob = 0.0
        ml_score = static_score
        ml_level = static_level
        ml_factors = []
        try:
            if ml_engine.model:
                ml_score, ml_level, ml_prob, ml_factors = ml_engine.predict_risk(deployment)
                deployment.ml_prediction_prob = ml_prob
                deployment.ml_used = True
                deployment.risk_score = ml_score
                deployment.risk_level = ml_level
        except Exception as e:
            logger.warning(f"[Sim] ML prediction failed: {e}")
            deployment.risk_score = static_score
            deployment.risk_level = static_level

        # Policy evaluation
        policy_decision_str = "ALLOW"
        policy_reasoning = []
        confidence = 0.0
        try:
            policy = evaluate_intelligent_policy(db_session=db, deployment=deployment, affected_modules=params.get("sensitive_files", []))
            policy_decision_str = policy.decision
            policy_reasoning = policy.reasoning
            confidence = policy.confidence_score
            deployment.deployment_decision = policy.decision
            deployment.policy_confidence_score = confidence
        except Exception as e:
            logger.warning(f"[Sim] Policy evaluation failed: {e}")

        # XAI breakdown
        xai_breakdown = {}
        try:
            xai_breakdown = xai_engine.generate_feature_impacts(deployment)
        except Exception:
            pass

        # Predict alerts
        predicted_alerts = []
        if (deployment.risk_score or 0) > 70:
            predicted_alerts.append({"type": "HIGH_RISK_DEPLOYMENT", "severity": "CRITICAL"})
        if deployment.historical_failures and deployment.historical_failures >= 3:
            predicted_alerts.append({"type": "REPEATED_FAILURES", "severity": "HIGH"})
        if deployment.has_auth_changes:
            predicted_alerts.append({"type": "SENSITIVE_MODULE_CHANGE", "severity": "WARNING"})

        # Persist simulation run
        sim_run = SimulationRun(
            simulation_name=sim_name,
            input_parameters=params,
            projected_risk_score=deployment.risk_score,
            projected_risk_level=deployment.risk_level,
            ml_failure_probability=ml_prob,
            policy_decision=policy_decision_str,
            policy_reasoning=policy_reasoning,
            predicted_alerts=predicted_alerts,
            confidence_score=confidence,
            xai_breakdown=xai_breakdown,
            created_by=created_by,
        )
        db.add(sim_run)
        db.commit()
        db.refresh(sim_run)

        result = {
            "simulation_id": sim_run.id,
            "simulation_name": sim_name,
            "input_parameters": params,
            "results": {
                "risk_score": deployment.risk_score,
                "risk_level": deployment.risk_level,
                "ml_failure_probability": round(ml_prob, 4),
                "policy_decision": policy_decision_str,
                "policy_reasoning": policy_reasoning,
                "confidence_score": round(confidence, 4),
                "predicted_alerts": predicted_alerts,
                "risk_factors": static_factors + ml_factors,
                "xai_feature_impacts": xai_breakdown,
            },
            "created_at": sim_run.created_at.isoformat() if sim_run.created_at else None,
        }

        logger.info(f"[Sim] completed id={sim_run.id} risk={deployment.risk_score} decision={policy_decision_str}")
        return result

    def get_simulation_history(self, db: Session, limit: int = 20) -> List[Dict[str, Any]]:
        sims = db.query(SimulationRun).order_by(SimulationRun.created_at.desc()).limit(limit).all()
        return [{
            "id": s.id, "name": s.simulation_name,
            "risk_score": s.projected_risk_score, "risk_level": s.projected_risk_level,
            "decision": s.policy_decision, "confidence": s.confidence_score,
            "ml_probability": s.ml_failure_probability,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        } for s in sims]

    def get_presets(self) -> List[Dict[str, Any]]:
        """Return simulation presets for common scenarios."""
        return [
            {"name": "Code Churn Spike", "description": "High code churn with many file changes", "params": {"code_churn": 800, "files_changed": 50, "commit_count": 20, "test_coverage": 60.0}},
            {"name": "Dependency Explosion", "description": "Many dependency updates at once", "params": {"dependency_updates": 15, "code_churn": 300, "test_coverage": 75.0}},
            {"name": "Auth Module Edit", "description": "Authentication module changes", "params": {"has_auth_changes": True, "sensitive_files": ["auth/login.py", "auth/tokens.py"], "code_churn": 150}},
            {"name": "Database Migration", "description": "Database schema migration", "params": {"has_db_migration": True, "sensitive_files": ["database/migrations/001.sql"], "files_changed": 5}},
            {"name": "Low Test Coverage", "description": "Deployment with minimal test coverage", "params": {"test_coverage": 20.0, "code_churn": 400, "files_changed": 25}},
            {"name": "Crisis Deployment", "description": "Emergency hotfix with high risk indicators", "params": {"code_churn": 500, "historical_failures": 4, "test_coverage": 30.0, "failure_rate_last_10": 0.4, "has_core_module_changes": True}},
        ]

simulation_engine = SimulationEngine()
