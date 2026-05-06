"""
Phase 11.3: Explainable AI (XAI) Engine.

Provides deep explainability for every deployment decision:
  - Feature impact analysis (SHAP-like coefficient decomposition)
  - Policy waterfall visualization (stage-by-stage decision trace)
  - Confidence breakdown (per-signal contribution)
  - Static vs ML weight analysis
  - Anomaly contribution scoring

Integrates with: ML Engine, Policy Engine, Meta-Learning service.
Persists explanations to PolicyExplanation table.
"""

import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session

from ..models.deployment import Deployment
from ..models.phase11_models import PolicyExplanation, AnomalyEvent
from ..config import settings

logger = logging.getLogger("aegis.xai")


class XAIEngine:
    """Explainable AI engine for deployment decision transparency."""

    def generate_feature_impacts(
        self,
        deployment: Deployment,
    ) -> Dict[str, float]:
        """
        Compute SHAP-like feature impact scores using LR coefficients.
        Returns feature_name → signed impact (positive = increases risk).
        """
        from .ml_engine import ml_engine, FEATURE_NAMES

        if not ml_engine.model:
            return {}

        try:
            features = ml_engine.prepare_features(deployment)
            scaler = ml_engine.model.named_steps["scaler"]
            classifier = ml_engine.model.named_steps["classifier"]

            # Get coefficients for the failure class
            if classifier.classes_[1] == 1:
                coefs = classifier.coef_[0]
            else:
                coefs = -classifier.coef_[0]

            scaled = scaler.transform([features])[0]

            impacts = {}
            for fname, scaled_val, coef in zip(FEATURE_NAMES, scaled, coefs):
                impact = round(float(scaled_val * coef), 4)
                impacts[fname] = impact

            return impacts

        except Exception as e:
            logger.warning(f"[XAI] feature_impact_failed: {e}")
            return {}

    def generate_policy_waterfall(
        self,
        deployment: Deployment,
        db: Optional[Session] = None,
    ) -> List[Dict[str, Any]]:
        """
        Generate a stage-by-stage policy waterfall showing how the decision was reached.
        Each stage shows: input state, rule evaluated, result, and decision mutation.
        """
        from .policy_engine import (
            PolicyContext, RISK_ALLOW_THRESHOLD, RISK_BLOCK_THRESHOLD,
            _has_sensitive_modifications, CONFIDENCE_LOW, CONFIDENCE_HIGH,
        )
        from .ml_engine import ml_engine
        from .alert_service import get_alerts_summary

        waterfall = []

        # Gather context data
        risk_score = deployment.risk_score or 0.0
        failure_prob = deployment.ml_prediction_prob or 0.0
        repo_name = deployment.repo_name or ""

        alerts_summary = {"max_severity": "LOW", "recent_alerts_count": 0}
        if db and repo_name:
            try:
                alerts_summary = get_alerts_summary(db, repo_name)
            except Exception:
                pass

        max_severity = alerts_summary.get("max_severity", "LOW")
        historical_failures = deployment.historical_failures or 0
        confidence = deployment.policy_confidence_score or 0.0
        decision_score = deployment.decision_score or 0.0

        # Parse sensitive files
        affected_modules = []
        if deployment.sensitive_files:
            try:
                affected_modules = json.loads(deployment.sensitive_files) if isinstance(deployment.sensitive_files, str) else deployment.sensitive_files
            except (json.JSONDecodeError, TypeError):
                pass

        current_decision = "ALLOW"

        # Stage 1: Risk Score Evaluation
        stage1_result = "PASS"
        if risk_score > RISK_BLOCK_THRESHOLD:
            stage1_result = "BLOCK"
            current_decision = "BLOCK"
        elif risk_score > RISK_ALLOW_THRESHOLD:
            stage1_result = "WARN"
            current_decision = "WARN"
        waterfall.append({
            "stage": 1,
            "name": "Risk Score Evaluation",
            "input": {"risk_score": risk_score, "block_threshold": RISK_BLOCK_THRESHOLD, "allow_threshold": RISK_ALLOW_THRESHOLD},
            "result": stage1_result,
            "decision_after": current_decision,
            "description": f"Risk score {risk_score:.1f} evaluated against thresholds (allow={RISK_ALLOW_THRESHOLD}, block={RISK_BLOCK_THRESHOLD})",
        })

        # Stage 2: ML Failure Probability
        stage2_result = "PASS"
        if failure_prob > 0.80:
            stage2_result = "BLOCK"
            current_decision = "BLOCK"
        elif failure_prob > 0.50:
            stage2_result = "WARN"
            if current_decision == "ALLOW":
                current_decision = "WARN"
        waterfall.append({
            "stage": 2,
            "name": "ML Failure Probability",
            "input": {"failure_probability": round(failure_prob, 4), "block_threshold": 0.80, "warn_threshold": 0.50},
            "result": stage2_result,
            "decision_after": current_decision,
            "description": f"ML predicts {failure_prob:.2%} failure probability",
        })

        # Stage 3: Alert Intelligence
        stage3_result = "PASS"
        if max_severity == "CRITICAL":
            stage3_result = "BLOCK"
            current_decision = "BLOCK"
        elif max_severity in ["HIGH", "MEDIUM"]:
            stage3_result = "WARN"
            if current_decision == "ALLOW":
                current_decision = "WARN"
        waterfall.append({
            "stage": 3,
            "name": "Alert Intelligence",
            "input": {"max_severity": max_severity, "recent_alerts": alerts_summary.get("recent_alerts_count", 0)},
            "result": stage3_result,
            "decision_after": current_decision,
            "description": f"Alert severity: {max_severity} with {alerts_summary.get('recent_alerts_count', 0)} recent alerts",
        })

        # Stage 4: Historical Failure Analysis
        stage4_result = "PASS"
        if historical_failures >= 3:
            stage4_result = "BLOCK"
            current_decision = "BLOCK"
        elif historical_failures >= 2:
            stage4_result = "WARN"
            if current_decision == "ALLOW":
                current_decision = "WARN"
        waterfall.append({
            "stage": 4,
            "name": "Historical Failure Analysis",
            "input": {"historical_failures": historical_failures, "block_threshold": 3},
            "result": stage4_result,
            "decision_after": current_decision,
            "description": f"{historical_failures} historical failures detected",
        })

        # Stage 5: Sensitive Module Detection
        has_sensitive = _has_sensitive_modifications(affected_modules)
        stage5_result = "ESCALATE" if has_sensitive else "PASS"
        if has_sensitive and current_decision == "ALLOW":
            current_decision = "WARN"
        elif has_sensitive and current_decision == "WARN":
            current_decision = "BLOCK"
        waterfall.append({
            "stage": 5,
            "name": "Sensitive Module Detection",
            "input": {"affected_modules": affected_modules[:5], "has_sensitive": has_sensitive},
            "result": stage5_result,
            "decision_after": current_decision,
            "description": f"{'Sensitive modules (auth/db/payments) modified' if has_sensitive else 'No sensitive modules affected'}",
        })

        # Stage 6: Confidence Override
        stage6_result = "PASS"
        if confidence < CONFIDENCE_LOW:
            stage6_result = "LOW_CONFIDENCE"
        elif confidence >= CONFIDENCE_HIGH:
            stage6_result = "HIGH_CONFIDENCE"
        waterfall.append({
            "stage": 6,
            "name": "Confidence Override Check",
            "input": {"confidence": round(confidence, 4), "low_threshold": CONFIDENCE_LOW, "high_threshold": CONFIDENCE_HIGH},
            "result": stage6_result,
            "decision_after": deployment.deployment_decision or current_decision,
            "description": f"Confidence score: {confidence:.2%} ({'low' if confidence < CONFIDENCE_LOW else 'high' if confidence >= CONFIDENCE_HIGH else 'moderate'})",
        })

        # Stage 7: Final Decision
        final_decision = deployment.deployment_decision or current_decision
        waterfall.append({
            "stage": 7,
            "name": "Final Policy Decision",
            "input": {"decision_score": round(decision_score, 2), "policy_version": deployment.policy_version or "9.3.1"},
            "result": final_decision,
            "decision_after": final_decision,
            "description": f"Final decision: {final_decision} (policy v{deployment.policy_version or '9.3.1'})",
        })

        return waterfall

    def generate_confidence_breakdown(
        self,
        deployment: Deployment,
        db: Optional[Session] = None,
    ) -> Dict[str, Any]:
        """
        Break down confidence score into its contributing signals.
        """
        from .alert_service import get_alerts_summary

        risk_score = deployment.risk_score or 0.0
        failure_prob = deployment.ml_prediction_prob or 0.0
        repo_name = deployment.repo_name or ""

        alerts_summary = {"max_severity": "LOW"}
        if db and repo_name:
            try:
                alerts_summary = get_alerts_summary(db, repo_name)
            except Exception:
                pass

        decision = deployment.deployment_decision or "ALLOW"
        max_severity = alerts_summary.get("max_severity", "LOW")

        # Signal 1: ML-Risk agreement
        ml_high = failure_prob >= 0.5
        risk_high = risk_score >= settings.RISK_ALLOW_THRESHOLD
        signal_1 = 0.35 if ml_high == risk_high else 0.08
        signal_1_label = "ML and Risk Score agree" if ml_high == risk_high else "ML and Risk Score disagree"

        # Signal 2: Alert-Decision agreement
        alert_high = max_severity in ["CRITICAL", "HIGH"]
        decision_restrictive = decision in ["BLOCK", "WARN"]
        signal_2 = 0.25 if alert_high == decision_restrictive else 0.05
        signal_2_label = "Alerts align with decision" if alert_high == decision_restrictive else "Alerts conflict with decision"

        # Signal 3: Data completeness
        complete = failure_prob > 0.0 and risk_score > 0.0
        signal_3 = 0.20 if complete else 0.05
        signal_3_label = "Full data available" if complete else "Incomplete data"

        # Signal 4: Adaptation status
        signal_4 = 0.15  # Default when adaptation is active
        signal_4_label = "Adaptive thresholds active"

        total = min(signal_1 + signal_2 + signal_3 + signal_4, 1.0)

        return {
            "total_confidence": round(total, 4),
            "signals": [
                {"name": "ML-Risk Agreement", "contribution": round(signal_1, 4), "max": 0.35, "description": signal_1_label},
                {"name": "Alert-Decision Alignment", "contribution": round(signal_2, 4), "max": 0.25, "description": signal_2_label},
                {"name": "Data Completeness", "contribution": round(signal_3, 4), "max": 0.20, "description": signal_3_label},
                {"name": "Adaptive Reliability", "contribution": round(signal_4, 4), "max": 0.15, "description": signal_4_label},
            ],
            "penalties": {
                "anomaly_penalty": 0.0,  # Would be computed from actual anomaly flags
                "cold_start_penalty": 0.10 if not deployment.ml_used else 0.0,
            },
        }

    def generate_static_vs_ml_analysis(
        self,
        deployment: Deployment,
    ) -> Dict[str, Any]:
        """Analyze the relative weights of static rules vs ML in the final decision."""
        ml_used = deployment.ml_used or False
        ml_prob = deployment.ml_prediction_prob or 0.0
        risk_score = deployment.risk_score or 0.0
        low_confidence = deployment.low_confidence_flag or False

        if not ml_used:
            return {
                "static_weight": 1.0,
                "ml_weight": 0.0,
                "blend_mode": "static_only",
                "description": "ML model not available — 100% static rule engine",
            }

        if low_confidence:
            return {
                "static_weight": 0.3,
                "ml_weight": 0.7,
                "blend_mode": "hybrid_fallback",
                "description": "Low ML confidence — blended 70% ML / 30% static rules",
            }

        return {
            "static_weight": 0.0,
            "ml_weight": 1.0,
            "blend_mode": "ml_primary",
            "description": "High ML confidence — ML-driven prediction with policy overrides",
        }

    def generate_full_explanation(
        self,
        deployment: Deployment,
        db: Optional[Session] = None,
        persist: bool = True,
    ) -> Dict[str, Any]:
        """
        Generate a complete XAI explanation package for a deployment.
        Optionally persists to the PolicyExplanation table.
        """
        feature_impacts = self.generate_feature_impacts(deployment)
        waterfall = self.generate_policy_waterfall(deployment, db)
        confidence = self.generate_confidence_breakdown(deployment, db)
        static_ml = self.generate_static_vs_ml_analysis(deployment)

        explanation = {
            "deployment_id": deployment.id,
            "decision": deployment.deployment_decision or "UNKNOWN",
            "risk_score": deployment.risk_score,
            "feature_impacts": feature_impacts,
            "waterfall_stages": waterfall,
            "confidence_breakdown": confidence,
            "static_vs_ml": static_ml,
            "anomaly_contributions": [],
            "generated_at": datetime.utcnow().isoformat(),
        }

        # Fetch anomaly contributions
        if db:
            try:
                anomalies = (
                    db.query(AnomalyEvent)
                    .filter(AnomalyEvent.deployment_id == deployment.id)
                    .all()
                )
                explanation["anomaly_contributions"] = [
                    {
                        "type": a.anomaly_type,
                        "description": a.description,
                        "impact_score": a.impact_score,
                        "contributing_features": a.contributing_features,
                    }
                    for a in anomalies
                ]
            except Exception:
                pass

        # Persist explanation
        if persist and db:
            try:
                pe = PolicyExplanation(
                    deployment_id=deployment.id,
                    decision=explanation["decision"],
                    waterfall_stages=waterfall,
                    feature_impacts=feature_impacts,
                    static_weight=static_ml.get("static_weight"),
                    ml_weight=static_ml.get("ml_weight"),
                    confidence_breakdown=confidence,
                    anomaly_contributions=explanation.get("anomaly_contributions"),
                )
                db.add(pe)
                db.commit()
            except Exception as e:
                logger.warning(f"[XAI] persist_failed: {e}")

        return explanation


# Singleton instance
xai_engine = XAIEngine()
