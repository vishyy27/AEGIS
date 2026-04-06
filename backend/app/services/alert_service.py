import json
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..models.alerts import Alert
from ..models.deployment import Deployment


SENSITIVE_MODULE_PREFIXES = ["auth/", "database/", "payments/", "credentials/", "config/"]

HISTORY_LIMIT = 10
ALERT_BURST_WINDOW_HOURS = 24
ALERT_BURST_THRESHOLD = 5


def _parse_json_field(value: Optional[str]) -> Any:
    if not value:
        return []
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return []


def _is_sensitive_file(file_path: str) -> bool:
    return any(file_path.startswith(prefix) for prefix in SENSITIVE_MODULE_PREFIXES)


def _has_sensitive_modifications(deployment: Deployment) -> bool:
    sensitive_files = _parse_json_field(deployment.sensitive_files)
    return any(_is_sensitive_file(f) for f in sensitive_files)


def analyze_deployment_history(db: Session, repo_name: str) -> List[Deployment]:
    if not repo_name:
        return []
    return (
        db.query(Deployment)
        .filter(Deployment.repo_name == repo_name)
        .order_by(Deployment.timestamp.desc())
        .limit(HISTORY_LIMIT)
        .all()
    )


def detect_high_risk_chain(
    deployments: List[Deployment],
) -> Optional[Dict[str, Any]]:
    if len(deployments) < 3:
        return None

    consecutive_count = 0
    chain_ids = []

    for dep in deployments:
        if dep.risk_score is not None and dep.risk_score > 70:
            consecutive_count += 1
            chain_ids.append(dep.id)
            if consecutive_count >= 3:
                return {
                    "type": "high_risk_chain",
                    "severity": "CRITICAL",
                    "chain_deployments": chain_ids[:consecutive_count],
                    "chain_length": consecutive_count,
                }
        else:
            break

    return None


def detect_failure_spikes(
    deployments: List[Deployment],
) -> Optional[Dict[str, Any]]:
    if len(deployments) < 4:
        return None

    current = deployments[0]
    baseline_deployments = deployments[1:6]

    if len(baseline_deployments) < 3:
        return None

    baseline_failures = [
        d.historical_failures for d in baseline_deployments
        if d.historical_failures is not None
    ]

    if not baseline_failures:
        return None

    avg_baseline = sum(baseline_failures) / len(baseline_failures)
    baseline_floor = max(avg_baseline, 1)

    current_failures = current.historical_failures or 0

    if current_failures > baseline_floor * 2:
        return {
            "type": "failure_spike",
            "severity": "HIGH",
            "current": current_failures,
            "baseline_avg": round(avg_baseline, 2),
            "multiplier": round(current_failures / baseline_floor, 2),
        }

    return None


def detect_deployment_instability(
    deployments: List[Deployment],
) -> Optional[Dict[str, Any]]:
    if len(deployments) < 3:
        return None

    eval_set = deployments[:5]
    risk_scores = [d.risk_score for d in eval_set if d.risk_score is not None]

    if len(risk_scores) < 3:
        return None

    avg_risk = sum(risk_scores) / len(risk_scores)
    high_risk_count = sum(1 for s in risk_scores if s > 60)

    if avg_risk > 65 and high_risk_count >= 3:
        return {
            "type": "deployment_instability",
            "severity": "HIGH",
            "avg_risk": round(avg_risk, 2),
            "high_risk_count": high_risk_count,
            "total_evaluated": len(risk_scores),
        }

    return None


def detect_alert_burst(
    db: Session, deployments: List[Deployment]
) -> Optional[Dict[str, Any]]:
    if not deployments:
        return None

    deployment_ids = [d.id for d in deployments[:HISTORY_LIMIT]]

    alerts_in_window = (
        db.query(Alert)
        .filter(Alert.deployment_id.in_(deployment_ids))
        .all()
    )

    twenty_four_hours_ago = datetime.utcnow() - timedelta(hours=ALERT_BURST_WINDOW_HOURS)
    alerts_24h = (
        db.query(Alert)
        .filter(Alert.timestamp >= twenty_four_hours_ago)
        .all()
    )

    if (
        len(alerts_in_window) > ALERT_BURST_THRESHOLD
        and len(alerts_24h) > ALERT_BURST_THRESHOLD
    ):
        return {
            "type": "alert_burst",
            "severity": "MEDIUM",
            "alert_count_10_deployments": len(alerts_in_window),
            "alert_count_24h": len(alerts_24h),
        }

    return None


def detect_sensitive_component_risk(
    deployments: List[Deployment],
) -> Optional[Dict[str, Any]]:
    if len(deployments) < 3:
        return None

    eval_set = deployments[:3]
    sensitive_count = sum(1 for d in eval_set if _has_sensitive_modifications(d))
    has_high_risk = any(
        d.risk_score is not None and d.risk_score > 60 for d in eval_set
    )

    if sensitive_count >= 2 and has_high_risk:
        severity = "CRITICAL" if sensitive_count == 3 else "HIGH"
        return {
            "type": "critical_component_risk",
            "severity": severity,
            "sensitive_deployments": sensitive_count,
            "total_evaluated": len(eval_set),
            "severity_escalated": sensitive_count == 3,
        }

    return None


def detect_risk_patterns(
    db: Session, deployments: List[Deployment]
) -> List[Dict[str, Any]]:
    patterns = []

    chain = detect_high_risk_chain(deployments)
    if chain:
        patterns.append(chain)

    spike = detect_failure_spikes(deployments)
    if spike:
        patterns.append(spike)

    instability = detect_deployment_instability(deployments)
    if instability:
        patterns.append(instability)

    burst = detect_alert_burst(db, deployments)
    if burst:
        patterns.append(burst)

    sensitive = detect_sensitive_component_risk(deployments)
    if sensitive:
        patterns.append(sensitive)

    return patterns


def _get_highest_severity(patterns: List[Dict[str, Any]]) -> str:
    severity_order = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "WARNING": 1, "LOW": 0}
    highest = "LOW"
    for p in patterns:
        sev = p.get("severity", "LOW")
        if severity_order.get(sev, 0) > severity_order.get(highest, 0):
            highest = sev
    return highest


def _is_duplicate_alert(
    db: Session, deployment_id: int, pattern_types: List[str]
) -> bool:
    one_hour_ago = datetime.utcnow() - timedelta(hours=1)
    existing = (
        db.query(Alert)
        .filter(
            Alert.deployment_id == deployment_id,
            Alert.timestamp >= one_hour_ago,
        )
        .all()
    )
    for alert in existing:
        if alert.incident_pattern:
            try:
                existing_patterns = json.loads(alert.incident_pattern)
                if isinstance(existing_patterns, list):
                    for ep in existing_patterns:
                        if isinstance(ep, dict) and ep.get("type") in pattern_types:
                            return True
                elif isinstance(existing_patterns, dict):
                    if existing_patterns.get("type") in pattern_types:
                        return True
            except (json.JSONDecodeError, TypeError):
                pass
    return False


def check_and_create_alert(
    db: Session, deployment_id: int, risk_score: float, historical_failures: int
) -> None:
    if risk_score > 70 or historical_failures > 3:
        alert_type = "HIGH_RISK_DEPLOYMENT" if risk_score > 70 else "FREQUENT_FAILURES"
        severity = "CRITICAL" if risk_score > 70 else "WARNING"
        message = f"Deployment risk threshold exceeded: {alert_type} (Score: {risk_score}, Failures: {historical_failures})"

        alert = Alert(
            deployment_id=deployment_id,
            alert_type=alert_type,
            severity=severity,
            message=message,
        )
        db.add(alert)
        db.commit()


def run_alert_intelligence_pipeline(db: Session, deployment: Deployment) -> None:
    repo_name = deployment.repo_name or ""

    if not repo_name:
        check_and_create_alert(
            db,
            deployment.id,
            deployment.risk_score or 0,
            deployment.historical_failures or 0,
        )
        return

    deployments = analyze_deployment_history(db, repo_name)

    if len(deployments) < 2:
        check_and_create_alert(
            db,
            deployment.id,
            deployment.risk_score or 0,
            deployment.historical_failures or 0,
        )
        return

    patterns = detect_risk_patterns(db, deployments)

    if not patterns:
        check_and_create_alert(
            db,
            deployment.id,
            deployment.risk_score or 0,
            deployment.historical_failures or 0,
        )
        return

    pattern_types = [p["type"] for p in patterns]

    if _is_duplicate_alert(db, deployment.id, pattern_types):
        return

    highest_severity = _get_highest_severity(patterns)
    pattern_names = ", ".join(p["type"].replace("_", " ").title() for p in patterns)
    message = f"Incident detected: {pattern_names}"

    alert = Alert(
        deployment_id=deployment.id,
        alert_type="INCIDENT_PATTERN",
        severity=highest_severity,
        message=message,
        incident_pattern=json.dumps(patterns),
        affected_service=repo_name,
    )
    db.add(alert)
    db.commit()
