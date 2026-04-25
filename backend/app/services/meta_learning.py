"""
Production-Grade Meta-Learning Layer for AEGIS Policy Engine.
(Phase 9.3 + Final Refinement)

Enhancements over 9.3:
  - Active reward/punishment signal weight learning (replaces passive EMA only)
  - Signal correlation detection (3 named patterns → weight deltas)
  - Long-term per-service behavioral memory (no new tables)
  - Proportional anomaly severity (impact_score ∈ [0, 1], not binary)
  - Dynamic score block threshold (precision/recall/anomaly-frequency driven)
  - All new features wrapped in try/except with graceful 9.3 fallback

One-way dependency: never imports from policy_engine.
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
POLICY_VERSION = "9.3.1"

# ---------------------------------------------------------------------------
# Static default signal weights (cold-start)
# ---------------------------------------------------------------------------
DEFAULT_WEIGHTS: Dict[str, float] = {
    "ml_failure_probability":  0.35,
    "risk_score":              0.30,
    "alert_severity":          0.20,
    "historical_failure_rate": 0.15,
}

WEIGHT_BOUNDS: Dict[str, Tuple[float, float]] = {
    "ml_failure_probability":  (0.10, 0.60),
    "risk_score":              (0.10, 0.55),
    "alert_severity":          (0.05, 0.40),
    "historical_failure_rate": (0.05, 0.35),
}

# ---------------------------------------------------------------------------
# Learning & stability constants
# ---------------------------------------------------------------------------
EMA_ALPHA             = 0.15   # Passive EMA smoothing (existing, retained)
ACTIVE_LR             = 0.02   # Active learning rate per reward/punishment step
MAX_WEIGHT_STEP       = 0.05   # Hard cap on any single weight adjustment
THRESHOLD_EMA_ALPHA   = 0.10   # EMA smoothing for dynamic block threshold
THRESHOLD_MIN         = 60.0   # Floor on dynamic score block threshold
THRESHOLD_MAX         = 88.0   # Ceiling on dynamic score block threshold
COLD_START_THRESHOLD  = 30     # Min evaluated deployments to enable adaptive learning
CORRELATION_THRESHOLD = 60     # Min evaluated for correlation pattern detection
DECAY_LAMBDA          = 0.05   # Recency decay: e^(-λ×days), half-life ≈ 14 days

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

def _recency_weight(ts: Optional[datetime]) -> float:
    if ts is None:
        return 0.5
    age = (datetime.utcnow() - ts).total_seconds() / 86400.0
    return math.exp(-DECAY_LAMBDA * max(age, 0.0))


def _normalize(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(0.0, min(1.0, (value - lo) / (hi - lo))) if hi > lo else 0.0


def _clamp_and_normalize_weights(weights: Dict[str, float]) -> Dict[str, float]:
    clamped = {}
    for k, v in weights.items():
        lo, hi = WEIGHT_BOUNDS.get(k, (0.05, 0.60))
        clamped[k] = max(lo, min(hi, v))
    total = sum(clamped.values())
    if total == 0:
        return dict(DEFAULT_WEIGHTS)
    return {k: round(v / total, 4) for k, v in clamped.items()}


def _count_evaluated(db: Session) -> int:
    from ..models.deployment import Deployment as M
    return db.query(M).filter(M.prediction_correct.isnot(None)).count()


def _empty_service_memory() -> Dict[str, Any]:
    return {
        "avg_risk_score_30d": 50.0,
        "failure_rate_30d":   0.0,
        "avg_decision_score": 50.0,
        "dominant_anomaly":   None,
        "chronic_modules":    [],
        "block_tp_rate":      0.5,
        "allow_fn_rate":      0.0,
        "avg_confidence":     0.5,
        "evaluated_count":    0,
    }


# ---------------------------------------------------------------------------
# 1. Active Signal Weight Learning
# ---------------------------------------------------------------------------

def compute_signal_weights(db: Session, limit: int = 50) -> Dict[str, float]:
    """
    Combines passive EMA reliability scoring with active reward/punishment learning.

    For each evaluated deployment (oldest → newest):
      - Correct signal vote → reward:  Δw = +ACTIVE_LR × (1 − w)
      - Incorrect signal vote → punish: Δw = −ACTIVE_LR × w
    Each step capped at MAX_WEIGHT_STEP.

    Final weight = 60% active + 40% EMA, then clamped and normalized.
    Returns DEFAULT_WEIGHTS on cold-start (< COLD_START_THRESHOLD records).
    """
    from ..models.deployment import Deployment as M

    evaluated = (
        db.query(M)
        .filter(
            M.prediction_correct.isnot(None),
            M.actual_outcome.isnot(None),
            M.predicted_failure.isnot(None),
        )
        .order_by(M.timestamp.desc())
        .limit(limit)
        .all()
    )

    if len(evaluated) < COLD_START_THRESHOLD:
        logger.info(
            f"[Meta:Final] cold_start=True n={len(evaluated)} "
            f"threshold={COLD_START_THRESHOLD} — using defaults"
        )
        return dict(DEFAULT_WEIGHTS)

    # --- Passive: decay-weighted reliability accumulation ---
    sig_correct: Dict[str, float] = {k: 0.0 for k in DEFAULT_WEIGHTS}
    sig_total:   Dict[str, float] = {k: 0.0 for k in DEFAULT_WEIGHTS}

    for dep in evaluated:
        rw = _recency_weight(dep.evaluation_timestamp)
        af = bool(dep.actual_outcome)

        def _accum(key: str, vote: bool) -> None:
            sig_total[key] += rw
            if vote == af:
                sig_correct[key] += rw

        if dep.ml_prediction_prob is not None:
            _accum("ml_failure_probability", dep.ml_prediction_prob >= 0.5)
        if dep.risk_score is not None:
            _accum("risk_score", dep.risk_score >= 40.0)
        if dep.historical_failures is not None:
            _accum("alert_severity", dep.historical_failures > 0)
        if dep.failure_rate_last_10 is not None:
            _accum("historical_failure_rate", dep.failure_rate_last_10 >= 0.3)

    reliability = {
        k: (sig_correct[k] / sig_total[k] if sig_total[k] > 0 else 0.5)
        for k in DEFAULT_WEIGHTS
    }
    ema_weights = {
        k: DEFAULT_WEIGHTS[k] * (1 - EMA_ALPHA) + reliability[k] * EMA_ALPHA
        for k in DEFAULT_WEIGHTS
    }

    # --- Active: reward/punishment pass (oldest → newest) ---
    active = dict(DEFAULT_WEIGHTS)
    for dep in reversed(evaluated):
        af = bool(dep.actual_outcome)

        def _step(key: str, vote: bool) -> None:
            w = active[key]
            delta = ACTIVE_LR * (1.0 - w) if (vote == af) else -ACTIVE_LR * w
            delta = max(-MAX_WEIGHT_STEP, min(MAX_WEIGHT_STEP, delta))
            active[key] = w + delta

        if dep.ml_prediction_prob is not None:
            _step("ml_failure_probability", dep.ml_prediction_prob >= 0.5)
        if dep.risk_score is not None:
            _step("risk_score", dep.risk_score >= 40.0)
        if dep.historical_failures is not None:
            _step("alert_severity", dep.historical_failures > 0)
        if dep.failure_rate_last_10 is not None:
            _step("historical_failure_rate", dep.failure_rate_last_10 >= 0.3)

    # Blend: 60% active + 40% EMA
    blended = {k: 0.60 * active[k] + 0.40 * ema_weights[k] for k in DEFAULT_WEIGHTS}
    result = _clamp_and_normalize_weights(blended)
    logger.info(f"[Meta:Final] weights={result} reliability={reliability}")
    return result


# ---------------------------------------------------------------------------
# 2. Signal Correlation Detection
# ---------------------------------------------------------------------------

def detect_signal_correlations(db: Session, limit: int = 100) -> Dict[str, float]:
    """
    Detect systematic cross-signal patterns from evaluated deployments.
    Returns per-signal weight deltas (applied on top of computed weights).
    Active only when evaluated_count >= CORRELATION_THRESHOLD.

    Patterns:
      ML_HIGH_ALERT_LOW_FP  → ML over-predicts; reduce ML, boost alert
      ALERT_HIGH_ML_LOW_FN  → Alerts more reliable; boost alert, reduce ML
      RISK_HIGH_ML_LOW_FP   → Rule engine over-fires; reduce risk_score weight
    """
    from ..models.deployment import Deployment as M

    adj: Dict[str, float] = {k: 0.0 for k in DEFAULT_WEIGHTS}

    rows = (
        db.query(M)
        .filter(
            M.prediction_correct.isnot(None),
            M.actual_outcome.isnot(None),
            M.ml_prediction_prob.isnot(None),
        )
        .order_by(M.timestamp.desc())
        .limit(limit)
        .all()
    )

    if len(rows) < CORRELATION_THRESHOLD:
        return adj

    ml_fp_cnt = alert_fn_cnt = risk_fp_cnt = 0
    for dep in rows:
        ml   = dep.ml_prediction_prob or 0.0
        risk = dep.risk_score or 0.0
        fail = dep.historical_failures or 0
        af   = bool(dep.actual_outcome)

        if ml >= 0.65 and fail <= 2 and not af:
            ml_fp_cnt += 1
        if fail > 2 and ml < 0.35 and af:
            alert_fn_cnt += 1
        if risk >= 65.0 and ml < 0.35 and not af:
            risk_fp_cnt += 1

    n = len(rows)
    if ml_fp_cnt / n >= 0.10:
        adj["ml_failure_probability"] -= 0.05
        adj["alert_severity"]         += 0.05
        logger.info(f"[Meta:Final] correlation=ML_FP rate={ml_fp_cnt/n:.3f}")

    if alert_fn_cnt / n >= 0.10:
        adj["alert_severity"]         += 0.05
        adj["ml_failure_probability"] -= 0.05
        logger.info(f"[Meta:Final] correlation=ALERT_FN rate={alert_fn_cnt/n:.3f}")

    if risk_fp_cnt / n >= 0.10:
        adj["risk_score"] -= 0.03
        logger.info(f"[Meta:Final] correlation=RISK_FP rate={risk_fp_cnt/n:.3f}")

    return adj


# ---------------------------------------------------------------------------
# 3. Long-Term Service Memory
# ---------------------------------------------------------------------------

def get_service_memory(db: Session, repo_name: str, limit: int = 200) -> Dict[str, Any]:
    """
    Per-service behavioral profile derived entirely from existing Deployment rows.
    No new DB tables or migrations required.

    Computes:
      A. Service Risk Profile (30-day rolling)
      B. Chronic High-Risk Modules (modules in ≥3 high-risk deployments)
      C. Decision Effectiveness (BLOCK TP rate, ALLOW FN rate, avg confidence)
    """
    from ..models.deployment import Deployment as M

    if not repo_name:
        return _empty_service_memory()

    cutoff = datetime.utcnow() - timedelta(days=30)
    recent = (
        db.query(M)
        .filter(M.repo_name == repo_name, M.timestamp >= cutoff)
        .order_by(M.timestamp.desc())
        .limit(limit)
        .all()
    )

    if not recent:
        return _empty_service_memory()

    # --- A. Service Risk Profile ---
    risks     = [d.risk_score for d in recent if d.risk_score is not None]
    dec_scores = [d.decision_score for d in recent if d.decision_score is not None]
    fail_list  = [d for d in recent if d.actual_outcome]

    avg_risk         = sum(risks) / len(risks) if risks else 50.0
    avg_dec          = sum(dec_scores) / len(dec_scores) if dec_scores else 50.0
    failure_rate_30d = len(fail_list) / len(recent) if recent else 0.0

    # --- B. Chronic High-Risk Modules ---
    module_cnt: Dict[str, int] = {}
    for dep in recent:
        if dep.risk_score and dep.risk_score >= 65.0 and dep.sensitive_files:
            try:
                files = (
                    json.loads(dep.sensitive_files)
                    if isinstance(dep.sensitive_files, str)
                    else dep.sensitive_files
                )
                for f in (files or []):
                    module_cnt[f] = module_cnt.get(f, 0) + 1
            except Exception:
                pass

    chronic = [m for m, cnt in module_cnt.items() if cnt >= 3]

    # --- C. Decision Effectiveness Profile ---
    evaluated  = [d for d in recent if d.prediction_correct is not None]
    blocks     = [d for d in evaluated if d.deployment_decision == "BLOCK"]
    allows     = [d for d in evaluated if d.deployment_decision == "ALLOW"]

    block_tp_rate = (
        sum(1 for d in blocks if d.actual_outcome) / len(blocks) if blocks else 0.5
    )
    allow_fn_rate = (
        sum(1 for d in allows if d.actual_outcome) / len(allows) if allows else 0.0
    )
    conf_vals  = [d.policy_confidence_score for d in evaluated if d.policy_confidence_score is not None]
    avg_conf   = sum(conf_vals) / len(conf_vals) if conf_vals else 0.5

    return {
        "avg_risk_score_30d": round(avg_risk, 2),
        "failure_rate_30d":   round(failure_rate_30d, 4),
        "avg_decision_score": round(avg_dec, 2),
        "dominant_anomaly":   None,
        "chronic_modules":    chronic,
        "block_tp_rate":      round(block_tp_rate, 4),
        "allow_fn_rate":      round(allow_fn_rate, 4),
        "avg_confidence":     round(avg_conf, 4),
        "evaluated_count":    len(evaluated),
    }


# ---------------------------------------------------------------------------
# 4. Dynamic Decision Score Threshold
# ---------------------------------------------------------------------------

def compute_dynamic_score_threshold(
    db: Session,
    service_memory: Dict[str, Any],
    limit: int = 50,
) -> float:
    """
    Adaptive BLOCK threshold for the hybrid decision score.
    Driven by global precision/recall trends + service-level effectiveness.
    EMA-smoothed to prevent oscillation. Clamped to [THRESHOLD_MIN, THRESHOLD_MAX].
    """
    from ..services.ml_engine import analyze_prediction_error

    base  = 75.0
    total_adj = 0.0

    try:
        metrics = analyze_prediction_error(db, limit=limit)
        if not metrics["insufficient_data"]:
            p = metrics.get("precision") or 0.65
            r = metrics.get("recall")    or 0.70
            if p < 0.65:
                total_adj += (0.65 - p) * 10.0    # raise (reduce false blocks)
            if r < 0.70:
                total_adj -= (0.70 - r) * 10.0    # lower (catch more failures)
    except Exception as e:
        logger.warning(f"[Meta:Final] threshold_metrics_failed={e}")

    # Service-level failure rate pressure
    fr = service_memory.get("failure_rate_30d", 0.0)
    if fr > 0.20:
        total_adj -= 5.0   # service is failing often → lower threshold

    # Decision effectiveness adjustments
    if service_memory.get("block_tp_rate", 0.5) < 0.40:
        total_adj += 5.0   # blocks are often wrong → raise threshold
    if service_memory.get("allow_fn_rate", 0.0) > 0.15:
        total_adj -= 5.0   # allows letting failures through → lower threshold

    raw      = base + total_adj
    smoothed = raw * THRESHOLD_EMA_ALPHA + base * (1 - THRESHOLD_EMA_ALPHA)
    result   = round(max(THRESHOLD_MIN, min(THRESHOLD_MAX, smoothed)), 2)

    logger.info(
        f"[Meta:Final] dynamic_threshold base={base} adj={total_adj:.2f} "
        f"raw={raw:.2f} smoothed={result}"
    )
    return result


# ---------------------------------------------------------------------------
# 5. Proportional Anomaly Detection
# ---------------------------------------------------------------------------

def detect_pre_failure_anomalies(
    risk_score: float,
    ml_failure_probability: float,
    alert_severity_str: str,
    decision_score: float,
    db: Session,
    repo_name: str,
    service_memory: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """
    Detect pre-failure anomalies with proportional impact_score ∈ [0.0, 1.0].
    Escalation and confidence penalties are proportional to magnitude.
    """
    from ..models.deployment import Deployment as M

    anomalies: List[Dict[str, Any]] = []
    mem = service_memory or _empty_service_memory()

    # --- A. SPIKE: sigma-distance proportional impact ---
    try:
        recent = (
            db.query(M.risk_score)
            .filter(M.repo_name == repo_name, M.risk_score.isnot(None))
            .order_by(M.timestamp.desc())
            .limit(5)
            .all()
        )
        scores = [r[0] for r in recent if r[0] is not None]
        if len(scores) >= 3:
            baseline = mem.get("avg_risk_score_30d") or (sum(scores) / len(scores))
            mean     = sum(scores) / len(scores)
            std      = math.sqrt(sum((s - mean) ** 2 for s in scores) / len(scores))
            if std > 0 and (risk_score - baseline) > 2.0 * std:
                sigma    = (risk_score - baseline) / std
                impact   = round(min((sigma - 2.0) / 3.0, 1.0), 4)
                impact   = min(impact + (0.05 if mem.get("chronic_modules") else 0.0), 1.0)
                anomalies.append({
                    "type":         "SPIKE",
                    "severity":     "HIGH",
                    "impact_score": impact,
                    "description":  (
                        f"Risk score {risk_score:.1f} is {sigma:.1f}σ above "
                        f"service baseline ({baseline:.1f}) — impact {impact:.2f}"
                    ),
                    "escalation": impact > 0.30,
                })
    except Exception as e:
        logger.warning(f"[Meta:Final] spike_failed={e}")

    # --- B. DIVERGENCE: delta-magnitude proportional impact ---
    if ml_failure_probability >= 0.65 and alert_severity_str.upper() not in ("CRITICAL", "HIGH"):
        alert_enc = ALERT_SEVERITY_ENCODE.get(alert_severity_str.upper(), 0.0)
        delta     = abs(ml_failure_probability - alert_enc)
        impact    = round(min(delta / 0.5, 1.0), 4)
        anomalies.append({
            "type":         "DIVERGENCE",
            "severity":     "MEDIUM",
            "impact_score": impact,
            "description":  (
                f"ML prob high ({ml_failure_probability:.2f}) but alert "
                f"{alert_severity_str} — divergence {impact:.2f}"
            ),
            "escalation": False,
        })

    if risk_score >= 65.0 and ml_failure_probability < 0.30:
        delta  = abs(_normalize(risk_score, 0.0, 100.0) - ml_failure_probability)
        impact = round(min(delta / 0.5, 1.0), 4)
        anomalies.append({
            "type":         "DIVERGENCE",
            "severity":     "MEDIUM",
            "impact_score": impact,
            "description":  (
                f"Risk score elevated ({risk_score:.1f}) but ML low "
                f"({ml_failure_probability:.2f}) — divergence {impact:.2f}"
            ),
            "escalation": False,
        })

    # --- C. REVERSAL: score-magnitude proportional impact ---
    try:
        recent_dec = (
            db.query(M.deployment_decision)
            .filter(M.repo_name == repo_name, M.deployment_decision.isnot(None))
            .order_by(M.timestamp.desc())
            .limit(3)
            .all()
        )
        past = [r[0] for r in recent_dec if r[0]]
        if len(past) >= 3 and all(d == "ALLOW" for d in past) and decision_score >= 60.0:
            impact = round(min((decision_score - 60.0) / 40.0, 1.0), 4)
            anomalies.append({
                "type":         "REVERSAL",
                "severity":     "MEDIUM",
                "impact_score": impact,
                "description":  (
                    f"Last 3 deployments ALLOW but decision_score now "
                    f"{decision_score:.1f} — reversal impact {impact:.2f}"
                ),
                "escalation": impact > 0.50,
            })
    except Exception as e:
        logger.warning(f"[Meta:Final] reversal_failed={e}")

    return anomalies


# ---------------------------------------------------------------------------
# 6. Hybrid Decision Score
# ---------------------------------------------------------------------------

def compute_hybrid_decision_score(
    ml_failure_probability: float,
    risk_score: float,
    alert_severity_str: str,
    historical_failure_rate: float,
    weights: Dict[str, float],
) -> float:
    """Composite decision score ∈ [0.0, 100.0]. Confidence dampening applied by caller."""
    ml_norm   = _normalize(ml_failure_probability, 0.0, 1.0)
    risk_norm = _normalize(risk_score, 0.0, 100.0)
    alert_enc = ALERT_SEVERITY_ENCODE.get(alert_severity_str.upper(), 0.0)
    hist_norm = _normalize(historical_failure_rate, 0.0, 1.0)

    w = weights
    raw = (
        w.get("ml_failure_probability",   DEFAULT_WEIGHTS["ml_failure_probability"]) * ml_norm
        + w.get("risk_score",             DEFAULT_WEIGHTS["risk_score"])             * risk_norm
        + w.get("alert_severity",         DEFAULT_WEIGHTS["alert_severity"])         * alert_enc
        + w.get("historical_failure_rate", DEFAULT_WEIGHTS["historical_failure_rate"]) * hist_norm
    )
    return round(min(max(raw * 100.0, 0.0), 100.0), 2)


# ---------------------------------------------------------------------------
# 7. Meta Context Builder
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
    Aggregates all meta-learning intelligence into a single dict consumed by
    evaluate_intelligent_policy() in policy_engine.py.
    """
    cold_start            = True
    weights               = dict(DEFAULT_WEIGHTS)
    correlation_adj: Dict[str, float] = {k: 0.0 for k in DEFAULT_WEIGHTS}
    service_memory        = _empty_service_memory()
    score_block_threshold = 75.0

    if db is not None:
        # Service memory (always attempted)
        try:
            service_memory = get_service_memory(db, repo_name)
        except Exception as e:
            logger.warning(f"[Meta:Final] service_memory_failed={e}")

        # Adaptive weights + correlation
        try:
            n         = _count_evaluated(db)
            cold_start = n < COLD_START_THRESHOLD
            if not cold_start:
                weights = compute_signal_weights(db)
            if n >= CORRELATION_THRESHOLD:
                correlation_adj = detect_signal_correlations(db)
                for k in list(weights.keys()):
                    weights[k] = weights.get(k, DEFAULT_WEIGHTS[k]) + correlation_adj.get(k, 0.0)
                weights = _clamp_and_normalize_weights(weights)
        except Exception as e:
            logger.warning(f"[Meta:Final] weight_computation_failed={e}")

        # Dynamic score threshold
        try:
            score_block_threshold = compute_dynamic_score_threshold(db, service_memory)
        except Exception as e:
            logger.warning(f"[Meta:Final] dynamic_threshold_failed={e}")

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
                service_memory=service_memory,
            )
        except Exception as e:
            logger.warning(f"[Meta:Final] anomaly_detection_failed={e}")

    return {
        "signal_weights":          weights,
        "decision_score":          decision_score,
        "anomaly_flags":           anomalies,
        "policy_version":          POLICY_VERSION,
        "cold_start":              cold_start,
        "score_block_threshold":   score_block_threshold,
        "service_memory":          service_memory,
        "correlation_adjustments": correlation_adj,
    }


# ---------------------------------------------------------------------------
# 8. Threshold Version Fingerprinting
# ---------------------------------------------------------------------------

def compute_threshold_version(adaptive_thresholds: Dict[str, Any]) -> str:
    payload = json.dumps(
        {k: adaptive_thresholds.get(k) for k in sorted(adaptive_thresholds.keys())},
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode()).hexdigest()[:16]
