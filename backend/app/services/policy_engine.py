from typing import Dict, Any, List, Optional
from datetime import datetime
import json
from dataclasses import dataclass, field
import logging

from ..models.deployment import Deployment
from ..config import settings

logger = logging.getLogger(__name__)

RISK_ALLOW_THRESHOLD = settings.RISK_ALLOW_THRESHOLD
RISK_BLOCK_THRESHOLD = settings.RISK_BLOCK_THRESHOLD

SENSITIVE_MODULES = ["auth/", "database/", "payments/", "credentials/", "config/"]


@dataclass
class PolicyContext:
    risk_score: float
    failure_probability: float
    alerts_summary: Dict[str, Any]
    affected_modules: List[str]
    recommendations: List[str]
    deployment_history: List[Dict[str, Any]]
    historical_failures: int
    # Phase 9.2: adaptive thresholds pulled from adaptive engine
    adaptive_thresholds: Dict[str, Any] = field(default_factory=dict)


class PolicyDecision:
    def __init__(
        self,
        decision: str,
        risk_score: float,
        risk_level: str,
        reasoning: List[str],
        recommendations: List[str],
        message: str,
        confidence_score: float = 0.0,
        override_reason: Optional[str] = None,
        alert_severity: Optional[str] = None,
        affected_modules: Optional[List[str]] = None,
    ):
        self.decision = decision
        self.risk_score = risk_score
        self.risk_level = risk_level
        self.reasoning = reasoning
        self.recommendations = recommendations
        self.message = message
        self.confidence_score = round(confidence_score, 4)
        self.override_reason = override_reason
        self.alert_severity = alert_severity
        self.affected_modules = affected_modules or []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision": self.decision,
            "risk_score": self.risk_score,
            "risk_level": self.risk_level,
            "confidence_score": self.confidence_score,
            "reasoning": self.reasoning,
            "recommendations": self.recommendations,
            "message": self.message,
            "override_reason": self.override_reason,
            "alert_severity": self.alert_severity,
            "affected_modules": self.affected_modules,
        }


def _has_sensitive_modifications(affected_modules: List[str]) -> bool:
    if not affected_modules:
        return False
    return any(
        any(mod.startswith(prefix) for prefix in SENSITIVE_MODULES)
        for mod in affected_modules
    )


def _generate_recommendations(
    decision: str,
    risk_score: float,
    alert_severity: Optional[str],
) -> List[str]:
    recs = []
    if decision == "ALLOW":
        recs.append("Continue with standard monitoring")
    elif decision == "WARN":
        if risk_score > 60:
            recs.append("Consider canary deployment first")
        if alert_severity and alert_severity in ["HIGH", "CRITICAL"]:
            recs.append(f"Review {alert_severity} severity alerts")
        recs.append("Enable enhanced logging")
    elif decision == "BLOCK":
        recs.append("Address high-risk factors before deploying")
        recs.append("Consider breaking into smaller deployments")
        recs.append("Run additional manual QA checks")
    return recs


def _compute_confidence_score(
    context: PolicyContext,
    decision: str,
) -> float:
    """
    Phase 9.2: Compute a [0, 1] confidence score based on:
    - Agreement between ML prob, risk score, and alerts
    - Data completeness (are all signals present?)
    - Adaptive reliability (is adaptation active?)
    """
    signals = []

    # Signal 1: ML probability directional agreement with risk score
    ml_high = context.failure_probability >= 0.5
    risk_high = context.risk_score >= RISK_ALLOW_THRESHOLD
    if ml_high == risk_high:
        signals.append(0.40)  # strong agreement
    else:
        signals.append(0.10)  # disagreement — low confidence

    # Signal 2: Alert severity agreement
    max_severity = context.alerts_summary.get("max_severity", "LOW")
    alert_high = max_severity in ["CRITICAL", "HIGH"]
    if alert_high == (decision in ["BLOCK", "WARN"]):
        signals.append(0.25)
    else:
        signals.append(0.05)

    # Signal 3: Data completeness
    complete = (
        context.failure_probability > 0.0
        and len(context.alerts_summary) > 0
        and context.risk_score > 0.0
    )
    signals.append(0.20 if complete else 0.05)

    # Signal 4: Adaptive reliability
    adaptation_active = context.adaptive_thresholds.get("adaptation_active", False)
    signals.append(0.10 if not adaptation_active else 0.15)

    return round(min(sum(signals), 1.0), 4)


def determine_decision(context: PolicyContext) -> PolicyDecision:
    # Pull adaptive thresholds (fallback to config values if unavailable)
    adaptive = context.adaptive_thresholds
    eff_block_threshold = adaptive.get("risk_block_threshold", RISK_BLOCK_THRESHOLD)
    eff_allow_threshold = adaptive.get("risk_allow_threshold", RISK_ALLOW_THRESHOLD)
    eff_ml_block_prob   = adaptive.get("ml_block_probability", 0.80)
    adaptive_reasons    = adaptive.get("reasons", [])

    decision = "ALLOW"
    reasoning = []
    override_reason = None

    # 1. CRITICAL Alerts
    max_severity = context.alerts_summary.get("max_severity", "LOW")
    if max_severity == "CRITICAL":
        decision = "BLOCK"
        reasoning.append("Critical alerts detected for this service")
        override_reason = "CRITICAL alerts present"

    # 2. Repeated Failures
    elif context.historical_failures >= 3:
        decision = "BLOCK"
        reasoning.append(f"Repeated failures observed (>= 3 recent failures)")
        override_reason = "Repeated historical failures"

    # 3. ML Failure Probability (adaptive threshold)
    elif context.failure_probability > eff_ml_block_prob:
        decision = "BLOCK"
        reasoning.append(
            f"High ML failure probability detected "
            f"({context.failure_probability:.2f} > adaptive threshold {eff_ml_block_prob:.2f})"
        )
        override_reason = "ML prediction indicates BLOCK"

    # 4. Risk Score Threat (adaptive threshold)
    elif context.risk_score > eff_block_threshold:
        decision = "BLOCK"
        reasoning.append(
            f"Risk score ({context.risk_score}) exceeds adaptive block threshold ({eff_block_threshold})"
        )

    else:
        # 5a. Alert-based Warnings
        if max_severity in ["HIGH", "MEDIUM"]:
            decision = "WARN"
            reasoning.append(f"Elevated alert severity: {max_severity}")
            override_reason = f"Alert severity {max_severity}"

        # 5b. ML probability warning band (adaptive lower bound)
        ml_warn_low = eff_ml_block_prob - 0.30
        if ml_warn_low <= context.failure_probability <= eff_ml_block_prob:
            decision = "WARN"
            reasoning.append(
                f"Warning ML failure probability ({context.failure_probability:.2f}) "
                f"in danger band [{ml_warn_low:.2f}, {eff_ml_block_prob:.2f}]"
            )

        # 5c. Risk score warn band (adaptive allow → block)
        if eff_allow_threshold < context.risk_score <= eff_block_threshold:
            decision = "WARN"
            reasoning.append(
                f"Risk score ({context.risk_score}) in warning band "
                f"({eff_allow_threshold}, {eff_block_threshold}]"
            )

        # 6. Sensitivity Weighting
        if _has_sensitive_modifications(context.affected_modules):
            reasoning.append("Sensitive core modules modified (Auth/DB/Payments)")
            if decision == "ALLOW":
                decision = "WARN"
                override_reason = "Sensitive modules modified"
            elif decision == "WARN":
                decision = "BLOCK"
                override_reason = "Sensitive modules escalating warning to block"

    # Inject adaptive reasoning only when adaptation is active
    if adaptive.get("adaptation_active"):
        reasoning.extend(adaptive_reasons)

    if decision == "ALLOW" and not reasoning:
        reasoning.append("All indicators within acceptable bounds.")

    # Compute confidence score (Phase 9.2)
    confidence = _compute_confidence_score(context, decision)

    # Determine risk level
    risk_level = "LOW"
    if context.risk_score >= eff_block_threshold or decision == "BLOCK":
        risk_level = "HIGH"
    elif context.risk_score >= eff_allow_threshold or decision == "WARN":
        risk_level = "MEDIUM"

    base_messages = {
        "ALLOW": f"Deployment permitted. Risk score {context.risk_score:.1f} is acceptable.",
        "WARN": f"Deployment flagged with warnings. Risk score {context.risk_score:.1f} requires attention.",
        "BLOCK": f"Deployment blocked. Risk score {context.risk_score:.1f} or other factors exceed safe threshold.",
    }
    message = base_messages.get(decision, "Unknown decision")
    if override_reason:
        message += f" Override: {override_reason}"

    return PolicyDecision(
        decision=decision,
        risk_score=context.risk_score,
        risk_level=risk_level,
        reasoning=reasoning,
        recommendations=_generate_recommendations(decision, context.risk_score, max_severity),
        message=message,
        confidence_score=confidence,
        override_reason=override_reason,
        alert_severity=max_severity if max_severity != "LOW" else None,
        affected_modules=context.affected_modules,
    )


def evaluate_intelligent_policy(
    db_session: Any,
    deployment: Deployment,
    affected_modules: Optional[List[str]] = None,
    risk_score: float = 0.0,
    historical_failures: int = 0,
) -> PolicyDecision:
    """Build PolicyContext with Phase 9.2 adaptive thresholds, then decide."""

    # ML Engine wrapper (graceful fallback)
    failure_prob = 0.0
    try:
        from .ml_engine import ml_engine
        if ml_engine.model:
            _, _, failure_prob, _ = ml_engine.predict_risk(deployment)
    except Exception as e:
        logger.warning(f"[Policy:9.2] ML prediction failed: {e}. Using 0.0")

    # Alert Service wrapper (graceful fallback)
    alerts_summary = {"max_severity": "LOW", "recent_alerts_count": 0, "spikes_detected": False}
    repo_name = deployment.repo_name if deployment else ""
    try:
        if db_session and repo_name:
            from .alert_service import get_alerts_summary
            alerts_summary = get_alerts_summary(db_session, repo_name)
    except Exception as e:
        logger.warning(f"[Policy:9.2] Alert service failed: {e}. Using empty summary.")

    # Phase 9.2: Fetch adaptive thresholds (graceful fallback)
    adaptive_thresholds: Dict[str, Any] = {}
    try:
        if db_session:
            from .ml_engine import get_adaptive_thresholds
            adaptive_thresholds = get_adaptive_thresholds(db_session, limit=50)
    except Exception as e:
        logger.warning(f"[Policy:9.2] Adaptive thresholds unavailable: {e}. Using defaults.")

    eff_risk_score = (
        deployment.risk_score if deployment and deployment.risk_score is not None else risk_score
    )
    eff_failures = (
        deployment.historical_failures
        if deployment and deployment.historical_failures is not None
        else historical_failures
    )

    context = PolicyContext(
        risk_score=eff_risk_score,
        failure_probability=failure_prob,
        alerts_summary=alerts_summary,
        affected_modules=affected_modules or [],
        recommendations=[],
        deployment_history=[],
        historical_failures=eff_failures,
        adaptive_thresholds=adaptive_thresholds,
    )

    decision = determine_decision(context)

    # Persist confidence score back to the deployment record (best-effort)
    if deployment and db_session:
        try:
            deployment.policy_confidence_score = decision.confidence_score
            db_session.commit()
        except Exception:
            pass

    return decision


def evaluate_from_analysis(
    db_session: Any,
    deployment: Deployment,
    risk_score: float,
    risk_level: str,
    risk_factors: List[str],
    alert_severity: Optional[str] = None,
    affected_modules: Optional[List[str]] = None,
    historical_failures: int = 0,
) -> PolicyDecision:
    """Adapter — backward-compatible entry for existing callers."""
    return evaluate_intelligent_policy(
        db_session=db_session,
        deployment=deployment,
        affected_modules=affected_modules or [],
        risk_score=risk_score,
        historical_failures=historical_failures,
    )


def evaluate_policy(
    deployment: Deployment,
    alert_severity: Optional[str] = None,
    affected_modules: Optional[List[str]] = None,
    db_session: Any = None,
) -> PolicyDecision:
    """Backward compatibility wrapper."""
    modules = affected_modules or []
    if deployment.sensitive_files:
        try:
            if isinstance(deployment.sensitive_files, str):
                modules = json.loads(deployment.sensitive_files)
            elif isinstance(deployment.sensitive_files, list):
                modules = deployment.sensitive_files
        except (json.JSONDecodeError, TypeError, AttributeError):
            pass

    return evaluate_intelligent_policy(
        db_session=db_session,
        deployment=deployment,
        affected_modules=modules,
    )