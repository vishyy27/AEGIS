"""
Phase 9.3: Meta-Learning Layer for AEGIS Policy Engine.

This module provides:
  - Adaptive per-signal reliability weighting with exponential decay
  - Hybrid composite decision scoring (weighted sum of normalized signals)
  - Pre-failure anomaly detection (SPIKE, DIVERGENCE, REVERSAL)
  - Policy versioning and threshold fingerprinting

Never imports from policy_engine — clean one-way dependency.
"""

import math
import hashlib
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple

from sqlalchemy.orm import Session

logger = logging.getLogger("aegis.meta")

# ---------------------------------------------------------------------------
# Versioning
# ---------------------------------------------------------------------------
POLICY_VERSION = "9.3.0"

# ---------------------------------------------------------------------------
# Static default signal weights (used during cold-start)
# ---------------------------------------------------------------------------
DEFAULT_WEIGHTS: Dict[str, float] = {
    "ml_failure_probability": 0.35,
    "risk_score":             0.30,
    "alert_severity":         0.20,
    "historical_failure_rate": 0.15,
}

# Per-signal clamping bounds [min, max]
WEIGHT_BOUNDS: Dict[str, Tuple[float, float]] = {
    "ml_failure_probability": (0.10, 0.60),
    "risk_score":             (0.10, 0.55),
    "alert_severity":         (0.05, 0.40),
    "historical_failure_rate": (0.05, 0.35),
}

# EMA smoothing factor — small α for stability
EMA_ALPHA = 0.15

# Minimum evaluated deployments to enable adaptive weighting
COLD_START_THRESHOLD = 30

# Decay half-life for recency weighting (days)
DECAY_LAMBDA = 0.05   # e^(-0.05 × 14) ≈ 0.50 → 50% weight at 14 days old

# Alert severity → [0, 1] encoding
ALERT_SEVERITY_ENCODE: Dict[str, float] = {
    "CRITICAL": 1.00,
    "HIGH":     0.75,
    "MEDIUM":   0.50,
    "WARNING":  0.25,
    "LOW":      0.00,
}

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _recency_weight(evaluation_timestamp: Optional[datetime]) -> float:
    """Exponential decay based on age of the deployment outcome."""
    if evaluation_timestamp is None:
        return 0.5  # treat as moderately old
    age_days = (datetime.utcnow() - evaluation_timestamp).total_seconds() / 86400.0
    return math.exp(-DECAY_LAMBDA * max(age_days, 0.0))


def _normalize(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    """Clamp + linear normalize value into [0, 1]."""
    return max(0.0, min(1.0, (value - lo) / (hi - lo))) if hi > lo else 0.0


def _clamp_and_normalize_weights(weights: Dict[str, float]) -> Dict[str, float]:
    """Apply per-signal bounds then renormalize so weights sum to 1.0."""
    clamped = {}
    for k, v in weights.items():
        lo, hi = WEIGHT_BOUNDS.get(k, (0.05, 0.60))
        clamped[k] = max(lo, min(hi, v))

    total = sum(clamped.values())
    if total == 0:
        return dict(DEFAULT_WEIGHTS)
    return {k: round(v / total, 4) for k, v in clamped.items()}


# ---------------------------------------------------------------------------
# 1. Signal Weight Computation (Meta-Learning)
# ---------------------------------------------------------------------------

def compute_signal_weights(db: Session, limit: int = 50) -> Dict[str, float]:
    """
    Compute per-signal reliability weights from evaluated deployments.

    For each signal we ask: "Did this signal's vote agree with the actual outcome?"
    Agreement rates are decay-weighted by recency, then EMA'd against defaults.

    Returns static DEFAULT_WEIGHTS on cold-start (< COLD_START_THRESHOLD records).
    """
    from ..models.deployment import Deployment as DeploymentModel

    evaluated = (
        db.query(DeploymentModel)
        .filter(
            DeploymentModel.prediction_correct.isnot(None),
            DeploymentModel.actual_outcome.isnot(None),
            DeploymentModel.predicted_failure.isnot(None),
        )
        .order_by(DeploymentModel.timestamp.desc())
        .limit(limit)
        .all()
    )

    if len(evaluated) < COLD_START_THRESHOLD:
        logger.info(
            f"[Meta:9.3] cold_start=True evaluated={len(evaluated)} "
            f"threshold={COLD_START_THRESHOLD} — using default weights"
        )
        return dict(DEFAULT_WEIGHTS)

    # Accumulate weighted votes per signal
    signal_correct_w: Dict[str, float] = {k: 0.0 for k in DEFAULT_WEIGHTS}
    signal_total_w:   Dict[str, float] = {k: 0.0 for k in DEFAULT_WEIGHTS}

    for dep in evaluated:
        rw = _recency_weight(dep.evaluation_timestamp)
        actual_failure = bool(dep.actual_outcome)

        # ML signal vote
        if dep.ml_prediction_prob is not None:
            ml_vote = dep.ml_prediction_prob >= 0.5
            signal_total_w["ml_failure_probability"]  += rw
            if ml_vote == actual_failure:
                signal_correct_w["ml_failure_probability"] += rw

        # Risk score signal vote (>= 40 = "risky")
        if dep.risk_score is not None:
            risk_vote = dep.risk_score >= 40.0
            signal_total_w["risk_score"]  += rw
            if risk_vote == actual_failure:
                signal_correct_w["risk_score"] += rw

        # Alert signal vote — use stored alert presence as proxy (best-effort)
        if dep.historical_failures is not None:
            alert_vote = dep.historical_failures > 0
            signal_total_w["alert_severity"]  += rw
            if alert_vote == actual_failure:
                signal_correct_w["alert_severity"] += rw

        # Historical failure rate signal vote
        if dep.failure_rate_last_10 is not None:
            hist_vote = dep.failure_rate_last_10 >= 0.3
            signal_total_w["historical_failure_rate"]  += rw
            if hist_vote == actual_failure:
                signal_correct_w["historical_failure_rate"] += rw

    # Compute reliability ∈ [0, 1] per signal
    reliability: Dict[str, float] = {}
    for k in DEFAULT_WEIGHTS:
        if signal_total_w[k] > 0:
            reliability[k] = signal_correct_w[k] / signal_total_w[k]
        else:
            reliability[k] = 0.5  # neutral when no data

    # EMA blend: new_weight = old_weight × (1 - α) + reliability × α
    blended: Dict[str, float] = {}
    for k, default_w in DEFAULT_WEIGHTS.items():
        blended[k] = default_w * (1 - EMA_ALPHA) + reliability[k] * EMA_ALPHA

    result = _clamp_and_normalize_weights(blended)
    logger.info(f"[Meta:9.3] weights_computed={result} reliability={reliability}")
    return result


# ---------------------------------------------------------------------------
# 2. Hybrid Decision Score
# ---------------------------------------------------------------------------

def compute_hybrid_decision_score(
    ml_failure_probability: float,
    risk_score: float,
    alert_severity_str: str,
    historical_failure_rate: float,
    weights: Dict[str, float],
) -> float:
    """
    Compute a composite decision score ∈ [0.0, 100.0] using adaptive signal weights.
    Higher score = higher risk.
    """
    ml_norm   = _normalize(ml_failure_probability, 0.0, 1.0)
    risk_norm = _normalize(risk_score, 0.0, 100.0)
    alert_enc = ALERT_SEVERITY_ENCODE.get(alert_severity_str.upper(), 0.0)
    hist_norm = _normalize(historical_failure_rate, 0.0, 1.0)

    w = weights
    raw = (
        w.get("ml_failure_probability", DEFAULT_WEIGHTS["ml_failure_probability"]) * ml_norm
        + w.get("risk_score",             DEFAULT_WEIGHTS["risk_score"])             * risk_norm
        + w.get("alert_severity",         DEFAULT_WEIGHTS["alert_severity"])         * alert_enc
        + w.get("historical_failure_rate", DEFAULT_WEIGHTS["historical_failure_rate"]) * hist_norm
    )
    return round(min(max(raw * 100.0, 0.0), 100.0), 2)


# ---------------------------------------------------------------------------
# 3. Pre-Failure Anomaly Detection
# ---------------------------------------------------------------------------

def detect_pre_failure_anomalies(
    risk_score: float,
    ml_failure_probability: float,
    alert_severity_str: str,
    decision_score: float,
    db: Session,
    repo_name: str,
) -> List[Dict[str, Any]]:
    """
    Phase 9.3: Detect three classes of pre-failure anomalies.
    Returns list of anomaly dicts with type, severity, description, escalation flag.
    """
    anomalies: List[Dict[str, Any]] = []

    # --- A. Risk Score SPIKE ---
    try:
        from ..models.deployment import Deployment as DeploymentModel
        recent = (
            db.query(DeploymentModel.risk_score)
            .filter(
                DeploymentModel.repo_name == repo_name,
                DeploymentModel.risk_score.isnot(None),
            )
            .order_by(DeploymentModel.timestamp.desc())
            .limit(5)
            .all()
        )
        scores = [r[0] for r in recent if r[0] is not None]
        if len(scores) >= 3:
            mean = sum(scores) / len(scores)
            variance = sum((s - mean) ** 2 for s in scores) / len(scores)
            std = math.sqrt(variance) if variance > 0 else 0.0
            if std > 0 and (risk_score - mean) > 2.0 * std:
                anomalies.append({
                    "type": "SPIKE",
                    "severity": "HIGH",
                    "description": (
                        f"Risk score {risk_score:.1f} is "
                        f"{((risk_score - mean) / std):.1f}σ above "
                        f"5-deployment service mean ({mean:.1f})"
                    ),
                    "escalation": True,
                })
    except Exception as e:
        logger.warning(f"[Meta:9.3] spike_detection_failed={e}")

    # --- B. Signal DIVERGENCE ---
    ml_high    = ml_failure_probability >= 0.65
    risk_high  = risk_score >= 65.0
    alert_high = alert_severity_str.upper() in ("CRITICAL", "HIGH")

    if ml_high and not alert_high:
        anomalies.append({
            "type": "DIVERGENCE",
            "severity": "MEDIUM",
            "description": (
                f"ML failure probability high ({ml_failure_probability:.2f}) "
                f"but alert severity is {alert_severity_str} — signal disagreement"
            ),
            "escalation": False,
        })

    if risk_high and ml_failure_probability < 0.30:
        anomalies.append({
            "type": "DIVERGENCE",
            "severity": "MEDIUM",
            "description": (
                f"Risk score elevated ({risk_score:.1f}) "
                f"but ML probability low ({ml_failure_probability:.2f}) — rule/ML disagreement"
            ),
            "escalation": False,
        })

    # --- C. Decision REVERSAL ---
    try:
        from ..models.deployment import Deployment as DeploymentModel
        recent_decisions = (
            db.query(DeploymentModel.deployment_decision)
            .filter(
                DeploymentModel.repo_name == repo_name,
                DeploymentModel.deployment_decision.isnot(None),
            )
            .order_by(DeploymentModel.timestamp.desc())
            .limit(3)
            .all()
        )
        past = [r[0] for r in recent_decisions if r[0]]
        if len(past) >= 3 and all(d == "ALLOW" for d in past) and decision_score >= 60.0:
            anomalies.append({
                "type": "REVERSAL",
                "severity": "MEDIUM",
                "description": (
                    f"Last 3 deployments were ALLOW but current decision_score "
                    f"is {decision_score:.1f} — behavioral pattern change detected"
                ),
                "escalation": True,
            })
    except Exception as e:
        logger.warning(f"[Meta:9.3] reversal_detection_failed={e}")

    return anomalies


# ---------------------------------------------------------------------------
# 4. Meta Context Builder (main entry point for policy_engine)
# ---------------------------------------------------------------------------

def build_meta_context(
    ml_failure_probability: float,
    risk_score: float,
    alert_severity_str: str,
    historical_failure_rate: float,
    db: Optional[Session],
    repo_name: str,
) -> Dict[str, Any]:
    """
    Aggregates all Phase 9.3 intelligence into a single meta dict consumed
    by `evaluate_intelligent_policy()` in policy_engine.py.

    Returns:
        signal_weights       — adaptive per-signal weights
        decision_score       — composite risk score [0–100]
        anomaly_flags        — list of anomaly dicts
        policy_version       — POLICY_VERSION constant
        cold_start           — True when insufficient feedback data
    """
    # Cold-start guard
    cold_start = True
    weights = dict(DEFAULT_WEIGHTS)

    if db is not None:
        try:
            evaluated_count = _count_evaluated(db)
            cold_start = evaluated_count < COLD_START_THRESHOLD
            if not cold_start:
                weights = compute_signal_weights(db)
        except Exception as e:
            logger.warning(f"[Meta:9.3] weight_computation_failed={e} — using defaults")

    decision_score = compute_hybrid_decision_score(
        ml_failure_probability=ml_failure_probability,
        risk_score=risk_score,
        alert_severity_str=alert_severity_str,
        historical_failure_rate=historical_failure_rate,
        weights=weights,
    )

    anomalies: List[Dict[str, Any]] = []
    if db is not None and repo_name:
        try:
            anomalies = detect_pre_failure_anomalies(
                risk_score=risk_score,
                ml_failure_probability=ml_failure_probability,
                alert_severity_str=alert_severity_str,
                decision_score=decision_score,
                db=db,
                repo_name=repo_name,
            )
        except Exception as e:
            logger.warning(f"[Meta:9.3] anomaly_detection_failed={e}")

    return {
        "signal_weights": weights,
        "decision_score": decision_score,
        "anomaly_flags": anomalies,
        "policy_version": POLICY_VERSION,
        "cold_start": cold_start,
    }


# ---------------------------------------------------------------------------
# 5. Threshold Version Fingerprinting
# ---------------------------------------------------------------------------

def compute_threshold_version(adaptive_thresholds: Dict[str, Any]) -> str:
    """SHA-256 fingerprint of current threshold state for audit tracing."""
    payload = json.dumps(
        {k: adaptive_thresholds.get(k) for k in sorted(adaptive_thresholds.keys())},
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _count_evaluated(db: Session) -> int:
    from ..models.deployment import Deployment as DeploymentModel
    return (
        db.query(DeploymentModel)
        .filter(DeploymentModel.prediction_correct.isnot(None))
        .count()
    )
