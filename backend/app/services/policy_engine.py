"""
Phase 9.3: Intelligent Policy Engine with Meta-Learning Integration.

Layers:
  Phase 9   – Core priority-based decision rules (safety anchor)
  Phase 9.1 – Alert intelligence + reasoning explainability
  Phase 9.2 – Adaptive thresholds from precision/recall feedback
  Phase 9.3 – Meta-learning: signal weights, hybrid scoring,
               confidence-aware overrides, anomaly escalation, trace logging
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import json
from dataclasses import dataclass, field
import logging

from ..models.deployment import Deployment
from ..config import settings

logger = logging.getLogger("aegis.policy")

RISK_ALLOW_THRESHOLD = settings.RISK_ALLOW_THRESHOLD
RISK_BLOCK_THRESHOLD = settings.RISK_BLOCK_THRESHOLD

SENSITIVE_MODULES = ["auth/", "database/", "payments/", "credentials/", "config/"]

# Confidence thresholds (Phase 9.3)
CONFIDENCE_LOW  = 0.45
CONFIDENCE_HIGH = 0.70


# ---------------------------------------------------------------------------
# Data objects
# ---------------------------------------------------------------------------

@dataclass
class PolicyContext:
    risk_score: float
    failure_probability: float
    alerts_summary: Dict[str, Any]
    affected_modules: List[str]
    recommendations: List[str]
    deployment_history: List[Dict[str, Any]]
    historical_failures: int
    # Phase 9.2
    adaptive_thresholds: Dict[str, Any] = field(default_factory=dict)
    # Phase 9.3
    signal_weights: Dict[str, float] = field(default_factory=dict)
    decision_score: float = 0.0
    anomaly_flags: List[Dict[str, Any]] = field(default_factory=list)
    policy_version: str = "9.3.0"
    cold_start: bool = True


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
        decision_score: float = 0.0,
        signal_weights: Optional[Dict[str, float]] = None,
        anomaly_flags: Optional[List[str]] = None,
        policy_version: str = "9.3.0",
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
        self.decision_score = round(decision_score, 2)
        self.signal_weights = signal_weights or {}
        self.anomaly_flags = anomaly_flags or []
        self.policy_version = policy_version
        self.override_reason = override_reason
        self.alert_severity = alert_severity
        self.affected_modules = affected_modules or []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision": self.decision,
            "risk_score": self.risk_score,
            "risk_level": self.risk_level,
            "confidence_score": self.confidence_score,
            "decision_score": self.decision_score,
            "signal_weights": self.signal_weights,
            "anomaly_flags": self.anomaly_flags,
            "policy_version": self.policy_version,
            "reasoning": self.reasoning,
            "recommendations": self.recommendations,
            "message": self.message,
            "override_reason": self.override_reason,
            "alert_severity": self.alert_severity,
            "affected_modules": self.affected_modules,
        }


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

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


def _compute_confidence_score(context: PolicyContext, decision: str) -> float:
    """
    Phase 9.3 enhanced confidence scoring.
    Incorporates anomaly detection penalties and cold-start penalty.
    """
    signals = []

    # Signal 1: ML ↔ risk score directional agreement
    ml_high   = context.failure_probability >= 0.5
    risk_high = context.risk_score >= RISK_ALLOW_THRESHOLD
    signals.append(0.35 if ml_high == risk_high else 0.08)

    # Signal 2: Alert ↔ decision agreement
    max_severity = context.alerts_summary.get("max_severity", "LOW")
    alert_high = max_severity in ["CRITICAL", "HIGH"]
    signals.append(0.25 if alert_high == (decision in ["BLOCK", "WARN"]) else 0.05)

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

    base = min(sum(signals), 1.0)

    # Phase 9.3: Anomaly penalty — each DIVERGENCE anomaly reduces confidence
    divergence_count = sum(
        1 for a in context.anomaly_flags if a.get("type") == "DIVERGENCE"
    )
    penalty = divergence_count * 0.10

    # Cold-start penalty
    if context.cold_start:
        penalty += 0.10

    return round(max(0.0, base - penalty), 4)


# ---------------------------------------------------------------------------
# Core decision logic
# ---------------------------------------------------------------------------

def _apply_core_rules(
    context: PolicyContext,
    eff_block_threshold: float,
    eff_allow_threshold: float,
    eff_ml_block_prob: float,
) -> tuple[str, List[str], Optional[str]]:
    """
    Phase 9.1 priority rule hierarchy — unchanged safety anchor.
    Returns (decision, reasoning, override_reason).
    """
    decision = "ALLOW"
    reasoning: List[str] = []
    override_reason = None
    max_severity = context.alerts_summary.get("max_severity", "LOW")

    # 1. CRITICAL Alerts
    if max_severity == "CRITICAL":
        decision = "BLOCK"
        reasoning.append("Critical alerts detected for this service")
        override_reason = "CRITICAL alerts present"

    # 2. Repeated Failures
    elif context.historical_failures >= 3:
        decision = "BLOCK"
        reasoning.append("Repeated failures observed (>= 3 recent failures)")
        override_reason = "Repeated historical failures"

    # 3. ML failure probability (adaptive)
    elif context.failure_probability > eff_ml_block_prob:
        decision = "BLOCK"
        reasoning.append(
            f"High ML failure probability "
            f"({context.failure_probability:.2f} > adaptive threshold {eff_ml_block_prob:.2f})"
        )
        override_reason = "ML prediction indicates BLOCK"

    # 4. Risk score threat (adaptive)
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

        # 5b. ML danger band
        ml_warn_low = eff_ml_block_prob - 0.30
        if ml_warn_low <= context.failure_probability <= eff_ml_block_prob:
            decision = "WARN"
            reasoning.append(
                f"ML probability ({context.failure_probability:.2f}) "
                f"in warning band [{ml_warn_low:.2f}, {eff_ml_block_prob:.2f}]"
            )

        # 5c. Risk score warn band
        if eff_allow_threshold < context.risk_score <= eff_block_threshold:
            decision = "WARN"
            reasoning.append(
                f"Risk score ({context.risk_score}) in warning band "
                f"({eff_allow_threshold}, {eff_block_threshold}]"
            )

        # 6. Sensitivity weighting
        if _has_sensitive_modifications(context.affected_modules):
            reasoning.append("Sensitive core modules modified (Auth/DB/Payments)")
            if decision == "ALLOW":
                decision = "WARN"
                override_reason = "Sensitive modules modified"
            elif decision == "WARN":
                decision = "BLOCK"
                override_reason = "Sensitive modules escalating warning to block"

    return decision, reasoning, override_reason


def _apply_anomaly_escalations(
    decision: str,
    reasoning: List[str],
    anomaly_flags: List[Dict[str, Any]],
) -> tuple[str, List[str]]:
    """Phase 9.3: Escalate decision if any anomaly has escalation=True."""
    for anomaly in anomaly_flags:
        if anomaly.get("escalation"):
            desc = anomaly.get("description", "")
            reasoning.append(f"Anomaly [{anomaly['type']}]: {desc}")
            if decision == "ALLOW":
                decision = "WARN"
            elif decision == "WARN":
                decision = "BLOCK"
            break  # one step per evaluation
    return decision, reasoning


def _apply_confidence_overrides(
    decision: str,
    reasoning: List[str],
    confidence: float,
    decision_score: float,
) -> tuple[str, str, List[str]]:
    """
    Phase 9.3: Confidence-aware override table.
    Returns (new_decision, override_reason_or_None, reasoning).
    """
    override_reason = None

    if confidence < CONFIDENCE_LOW:
        if decision == "ALLOW":
            reasoning.append(
                f"Confidence-override: ALLOW → WARN (low confidence {confidence:.2f})"
            )
            decision = "WARN"
            override_reason = "Low confidence upgrade"
        elif decision == "WARN" and decision_score >= 60.0:
            reasoning.append(
                f"Confidence-override: WARN → BLOCK "
                f"(low confidence {confidence:.2f} + decision_score {decision_score:.1f} ≥ 60)"
            )
            decision = "BLOCK"
            override_reason = "Low confidence + high score escalation"
        elif decision == "BLOCK" and decision_score < 40.0:
            reasoning.append(
                f"Confidence-override: BLOCK → WARN "
                f"(very low confidence {confidence:.2f} + decision_score {decision_score:.1f} < 40)"
            )
            decision = "WARN"
            override_reason = "Low confidence over-block prevention"

    elif confidence >= CONFIDENCE_HIGH:
        if decision == "WARN" and decision_score < 45.0:
            reasoning.append(
                f"Confidence-override: WARN → ALLOW "
                f"(high confidence {confidence:.2f} + decision_score {decision_score:.1f} < 45)"
            )
            decision = "ALLOW"
            override_reason = "High confidence safe downgrade"

    return decision, override_reason, reasoning


def _apply_decision_score_guidance(
    decision: str,
    reasoning: List[str],
    decision_score: float,
) -> tuple[str, List[str]]:
    """Phase 9.3: Hybrid score can escalate within the intermediate zone."""
    if decision == "WARN" and decision_score >= 75.0:
        decision = "BLOCK"
        reasoning.append(
            f"Meta-learning: decision_score {decision_score:.1f} ≥ 75 escalates WARN → BLOCK"
        )
    return decision, reasoning


# ---------------------------------------------------------------------------
# Main decision function
# ---------------------------------------------------------------------------

def determine_decision(context: PolicyContext) -> PolicyDecision:
    adaptive          = context.adaptive_thresholds
    eff_block         = adaptive.get("risk_block_threshold", RISK_BLOCK_THRESHOLD)
    eff_allow         = adaptive.get("risk_allow_threshold", RISK_ALLOW_THRESHOLD)
    eff_ml_block_prob = adaptive.get("ml_block_probability", 0.80)
    adaptive_reasons  = adaptive.get("reasons", [])

    # Stage 1: Core priority rules (safety anchor)
    decision, reasoning, override_reason = _apply_core_rules(
        context, eff_block, eff_allow, eff_ml_block_prob
    )

    # Stage 2: Anomaly escalation
    decision, reasoning = _apply_anomaly_escalations(
        decision, reasoning, context.anomaly_flags
    )

    # Stage 3: Hybrid decision_score guidance (intermediate zone only)
    if decision not in ("BLOCK",) or override_reason is None:
        decision, reasoning = _apply_decision_score_guidance(
            decision, reasoning, context.decision_score
        )

    # Stage 4: Confidence-aware overrides
    initial_confidence = _compute_confidence_score(context, decision)
    decision, conf_override, reasoning = _apply_confidence_overrides(
        decision, reasoning, initial_confidence, context.decision_score
    )
    if conf_override:
        override_reason = conf_override

    # Inject adaptive reasoning
    if adaptive.get("adaptation_active"):
        reasoning.extend(adaptive_reasons)

    if not reasoning:
        reasoning.append("All indicators within acceptable bounds.")

    # Final confidence after all mutations
    final_confidence = _compute_confidence_score(context, decision)

    # Risk level
    risk_level = "LOW"
    if context.risk_score >= eff_block or decision == "BLOCK":
        risk_level = "HIGH"
    elif context.risk_score >= eff_allow or decision == "WARN":
        risk_level = "MEDIUM"

    max_severity = context.alerts_summary.get("max_severity", "LOW")
    base_messages = {
        "ALLOW": f"Deployment permitted. Risk score {context.risk_score:.1f} is acceptable.",
        "WARN":  f"Deployment flagged with warnings. Risk score {context.risk_score:.1f} requires attention.",
        "BLOCK": f"Deployment blocked. Risk score {context.risk_score:.1f} or other factors exceed safe threshold.",
    }
    message = base_messages.get(decision, "Unknown decision")
    if override_reason:
        message += f" Override: {override_reason}"

    anomaly_flag_strs = [a.get("description", str(a)) for a in context.anomaly_flags]

    # Structured decision trace log
    logger.info(
        "[Policy:9.3] decision_trace=%s",
        json.dumps({
            "decision": decision,
            "decision_score": context.decision_score,
            "signal_weights": context.signal_weights,
            "confidence_score": final_confidence,
            "triggered_rules": reasoning,
            "anomaly_flags": anomaly_flag_strs,
            "policy_version": context.policy_version,
            "cold_start": context.cold_start,
        }),
    )

    return PolicyDecision(
        decision=decision,
        risk_score=context.risk_score,
        risk_level=risk_level,
        reasoning=reasoning,
        recommendations=_generate_recommendations(decision, context.risk_score, max_severity),
        message=message,
        confidence_score=final_confidence,
        decision_score=context.decision_score,
        signal_weights=context.signal_weights,
        anomaly_flags=anomaly_flag_strs,
        policy_version=context.policy_version,
        override_reason=override_reason,
        alert_severity=max_severity if max_severity != "LOW" else None,
        affected_modules=context.affected_modules,
    )


# ---------------------------------------------------------------------------
# Main entry points
# ---------------------------------------------------------------------------

def evaluate_intelligent_policy(
    db_session: Any,
    deployment: Deployment,
    affected_modules: Optional[List[str]] = None,
    risk_score: float = 0.0,
    historical_failures: int = 0,
) -> PolicyDecision:
    """Build full PolicyContext (9.3) then evaluate."""
    from .meta_learning import build_meta_context, compute_threshold_version

    # ML Engine (graceful fallback)
    failure_prob = 0.0
    try:
        from .ml_engine import ml_engine
        if ml_engine.model:
            _, _, failure_prob, _ = ml_engine.predict_risk(deployment)
    except Exception as e:
        logger.warning(f"[Policy:9.3] ML prediction failed: {e}")

    # Alert Service (graceful fallback)
    alerts_summary = {"max_severity": "LOW", "recent_alerts_count": 0, "spikes_detected": False}
    repo_name = (deployment.repo_name or "") if deployment else ""
    try:
        if db_session and repo_name:
            from .alert_service import get_alerts_summary
            alerts_summary = get_alerts_summary(db_session, repo_name)
    except Exception as e:
        logger.warning(f"[Policy:9.3] Alert service failed: {e}")

    # Adaptive thresholds with decay (Phase 9.3)
    adaptive_thresholds: Dict[str, Any] = {}
    try:
        if db_session:
            from .ml_engine import get_adaptive_thresholds
            adaptive_thresholds = get_adaptive_thresholds(db_session, limit=50, decay_factor=0.05)
    except Exception as e:
        logger.warning(f"[Policy:9.3] Adaptive thresholds unavailable: {e}")

    # Historical failure rate proxy
    hist_failure_rate = getattr(deployment, "failure_rate_last_10", None) or 0.0

    # Phase 9.3: Meta-learning context
    meta: Dict[str, Any] = {}
    try:
        meta = build_meta_context(
            ml_failure_probability=failure_prob,
            risk_score=deployment.risk_score if deployment and deployment.risk_score is not None else risk_score,
            alert_severity_str=alerts_summary.get("max_severity", "LOW"),
            historical_failure_rate=hist_failure_rate,
            db=db_session,
            repo_name=repo_name,
        )
    except Exception as e:
        logger.warning(f"[Policy:9.3] Meta-context build failed: {e}")

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
        signal_weights=meta.get("signal_weights", {}),
        decision_score=meta.get("decision_score", 0.0),
        anomaly_flags=meta.get("anomaly_flags", []),
        policy_version=meta.get("policy_version", "9.3.0"),
        cold_start=meta.get("cold_start", True),
    )

    policy_decision = determine_decision(context)

    # Persist 9.3 telemetry back to deployment (best-effort)
    if deployment and db_session:
        try:
            deployment.policy_confidence_score = policy_decision.confidence_score
            deployment.decision_score = policy_decision.decision_score
            deployment.policy_version = policy_decision.policy_version
            deployment.threshold_version = compute_threshold_version(adaptive_thresholds)
            db_session.commit()
        except Exception as e:
            logger.debug(f"[Policy:9.3] telemetry_persist_failed={e}")

    return policy_decision


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
    """Backward-compatible adapter for webhook router."""
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
    """Legacy backward-compatibility wrapper."""
    modules = affected_modules or []
    if deployment and deployment.sensitive_files:
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