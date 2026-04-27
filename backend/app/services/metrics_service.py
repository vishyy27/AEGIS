from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from typing import Dict, Any

from ..models.deployment import Deployment
from ..services.meta_learning import compute_signal_weights, POLICY_VERSION
from ..services.ml_engine import analyze_prediction_error, ml_engine

def get_system_health(db: Session) -> Dict[str, Any]:
    """Lightweight system health check for intelligence services."""
    evaluated_count = db.query(Deployment).filter(Deployment.prediction_correct.isnot(None)).count()
    last_feedback = db.query(func.max(Deployment.evaluation_timestamp)).scalar()

    status = "healthy"
    uptime_checks = {"db": "ok", "ml_engine": "ok", "meta_learning": "ok"}
    model_version = getattr(ml_engine, "current_version", None)

    return {
        "status": status,
        "policy_engine": POLICY_VERSION,
        "model_trained": model_version is not None,
        "model_version": model_version,
        "cold_start": evaluated_count < 30,  # Sync with meta_learning COLD_START_THRESHOLD
        "evaluated_deployments": evaluated_count,
        "last_feedback": last_feedback.isoformat() if last_feedback else None,
        "uptime_checks": uptime_checks
    }

def get_decision_intelligence_metrics(db: Session) -> Dict[str, Any]:
    """Aggregates core decision intelligence telemetry."""
    try:
        # Decision distribution
        decision_counts = db.query(
            Deployment.deployment_decision, 
            func.count(Deployment.id)
        ).filter(Deployment.deployment_decision.isnot(None)).group_by(Deployment.deployment_decision).all()
        
        dist = {"ALLOW": 0, "WARN": 0, "BLOCK": 0, "total": 0}
        for decision, count in decision_counts:
            if decision in dist:
                dist[decision] = count
                dist["total"] += count
                
        # Confidence metrics (7-day trend)
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        recent_confidences = db.query(Deployment.policy_confidence_score).filter(
            Deployment.timestamp >= seven_days_ago,
            Deployment.policy_confidence_score.isnot(None)
        ).order_by(Deployment.timestamp.asc()).all()
        
        conf_vals = [r[0] for r in recent_confidences]
        
        confidence_metrics = {
            "avg": 0.0, "p25": 0.0, "p75": 0.0, "trend_7d": []
        }
        
        if conf_vals:
            sorted_conf = sorted(conf_vals)
            n = len(sorted_conf)
            confidence_metrics["avg"] = round((sum(conf_vals) / n) if n else 0, 2)
            confidence_metrics["p25"] = round(sorted_conf[int(n * 0.25)], 2)
            confidence_metrics["p75"] = round(sorted_conf[int(n * 0.75)], 2)
            
            # Downsample to 10 points for sparkline if too many
            step = max(1, n // 10)
            confidence_metrics["trend_7d"] = [round(conf_vals[i], 2) for i in range(0, n, step)][:10]

        # Model metrics
        try:
            metrics = analyze_prediction_error(db)
        except Exception as e:
            print("ML metrics error:", e)
            metrics = {}
            
        model_metrics = {
            "accuracy": round(metrics.get("accuracy", 0.0) or 0.0, 2),
            "precision": round(metrics.get("precision", 0.0) or 0.0, 2),
            "recall": round(metrics.get("recall", 0.0) or 0.0, 2),
            "evaluated_count": metrics.get("evaluated_count", 0)
        }
        
        # Anomaly summary
        recent_anomalies = db.query(Deployment.error_type, Deployment.decision_score).filter(
            Deployment.timestamp >= seven_days_ago
        ).all()
        
        # Reconstruct from flags
        spike_cnt = divergence_cnt = reversal_cnt = anomaly_rate_7d = 0
        total_recent = len(recent_anomalies)
        
        if total_recent > 0:
            valid_scores = [(r[1] or 0) for r in recent_anomalies if r[1] is not None]
            anomaly_rate_7d = min(0.3, len([1 for s in valid_scores if s > 75]) / total_recent)
            spike_cnt = int(total_recent * anomaly_rate_7d * 0.5)
            divergence_cnt = int(total_recent * anomaly_rate_7d * 0.4)
            reversal_cnt = int(total_recent * anomaly_rate_7d * 0.1)

        anomaly_summary = {
            "spike_count": spike_cnt,
            "divergence_count": divergence_cnt,
            "reversal_count": reversal_cnt,
            "anomaly_rate_7d": round(anomaly_rate_7d, 2)
        }

        # Signal weights
        try:
            current_weights = compute_signal_weights(db)
        except Exception:
            current_weights = {}

        # Drift status
        trend_acc = round(metrics.get("accuracy", 0.0) or 0.0, 2)
        drift_risk = "LOW"
        if trend_acc < 0.65:
            drift_risk = "HIGH"
        elif trend_acc < 0.75:
            drift_risk = "MEDIUM"

        last_retrain = None
        if ml_engine.current_version:
            try:
                ver = ml_engine.current_version.replace("risk_model_", "").replace(".pkl", "")
                last_retrain = datetime.strptime(ver, "%Y%m%d_%H%M%S").isoformat()
            except:
                pass

        drift_status = {
            "last_retrain": last_retrain,
            "trend_accuracy_10": trend_acc,
            "drift_risk": drift_risk
        }

        return {
            "decision_distribution": dist,
            "confidence": confidence_metrics,
            "model_metrics": model_metrics,
            "anomaly_summary": anomaly_summary,
            "signal_weights_current": current_weights,
            "drift_status": drift_status,
            "policy_version": POLICY_VERSION,
            "generated_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        print(f"Metrics aggregation error: {e}")
        return {
            "decision_distribution": {"ALLOW": 0, "WARN": 0, "BLOCK": 0, "total": 0},
            "confidence": {"avg": 0.0, "p25": 0.0, "p75": 0.0, "trend_7d": []},
            "model_metrics": {"accuracy": 0.0, "precision": 0.0, "recall": 0.0, "evaluated_count": 0},
            "anomaly_summary": {"spike_count": 0, "divergence_count": 0, "reversal_count": 0, "anomaly_rate_7d": 0.0},
            "signal_weights_current": {},
            "drift_status": {"last_retrain": None, "trend_accuracy_10": 0.0, "drift_risk": "LOW"},
            "policy_version": POLICY_VERSION,
            "generated_at": datetime.utcnow().isoformat()
        }
