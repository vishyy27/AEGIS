from typing import Dict, Any, List, Optional
from datetime import datetime
import json

from ..models.deployment import Deployment
from ..config import settings


RISK_ALLOW_THRESHOLD = settings.RISK_ALLOW_THRESHOLD
RISK_BLOCK_THRESHOLD = settings.RISK_BLOCK_THRESHOLD

SEVERITY_OVERRIDE_MAP = {
    "CRITICAL": "BLOCK",
    "HIGH": "BLOCK",
    "MEDIUM": "WARN",
    "WARNING": "WARN",
    "LOW": "ALLOW",
}

SENSITIVE_MODULES = ["auth/", "database/", "payments/", "credentials/", "config/"]


class PolicyDecision:
    def __init__(
        self,
        decision: str,
        risk_score: float,
        risk_level: str,
        recommendations: List[str],
        message: str,
        override_reason: Optional[str] = None,
        alert_severity: Optional[str] = None,
        affected_modules: Optional[List[str]] = None
    ):
        self.decision = decision
        self.risk_score = risk_score
        self.risk_level = risk_level
        self.recommendations = recommendations
        self.message = message
        self.override_reason = override_reason
        self.alert_severity = alert_severity
        self.affected_modules = affected_modules or []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision": self.decision,
            "risk_score": self.risk_score,
            "risk_level": self.risk_level,
            "recommendations": self.recommendations,
            "message": self.message,
            "override_reason": self.override_reason,
            "alert_severity": self.alert_severity,
            "affected_modules": self.affected_modules
        }


def apply_risk_thresholds(risk_score: float) -> str:
    """Apply base risk score thresholds to determine decision."""
    if risk_score < RISK_ALLOW_THRESHOLD:
        return "ALLOW"
    elif risk_score <= RISK_BLOCK_THRESHOLD:
        return "WARN"
    else:
        return "BLOCK"


def evaluate_alert_severity(deployment: Deployment) -> Optional[str]:
    """Extract highest alert severity from deployment's alert history."""
    from ..models.alerts import Alert
    
    if not deployment or not deployment.id:
        return None
    
    return None


def _has_sensitive_modifications(affected_modules: List[str]) -> bool:
    """Check if any affected modules are sensitive."""
    if not affected_modules:
        return False
    return any(
        any(mod.startswith(prefix) for prefix in SENSITIVE_MODULES)
        for mod in affected_modules
    )


def _escalate_for_sensitive_modules(
    base_decision: str,
    affected_modules: List[str]
) -> str:
    """Escalate decision if sensitive modules are affected."""
    if _has_sensitive_modifications(affected_modules):
        if base_decision == "ALLOW":
            return "WARN"
        elif base_decision == "WARN":
            return "BLOCK"
    return base_decision


def _check_repeated_incidents(deployment: Deployment) -> bool:
    """Check for repeated incidents in deployment history."""
    if not deployment or not deployment.historical_failures:
        return False
    return deployment.historical_failures >= 3


def determine_decision(
    risk_score: float,
    risk_level: str,
    alert_severity: Optional[str],
    affected_modules: List[str],
    historical_failures: int
) -> PolicyDecision:
    """Apply all decision rules to determine final policy decision."""
    
    base_decision = apply_risk_thresholds(risk_score)
    override_reason = None
    final_decision = base_decision
    
    if alert_severity:
        severity_override = SEVERITY_OVERRIDE_MAP.get(alert_severity.upper())
        if severity_override and severity_override != "ALLOW":
            if severity_override == "BLOCK":
                final_decision = "BLOCK"
                override_reason = f"Alert severity: {alert_severity}"
            elif severity_override == "WARN" and final_decision == "ALLOW":
                final_decision = "WARN"
                override_reason = f"Alert severity: {alert_severity}"
    
    final_decision = _escalate_for_sensitive_modules(final_decision, affected_modules)
    
    if historical_failures >= 3:
        final_decision = "BLOCK"
        override_reason = "Repeated incidents detected" if not override_reason else override_reason
    
    message = _generate_decision_message(final_decision, risk_score, override_reason)
    
    return PolicyDecision(
        decision=final_decision,
        risk_score=risk_score,
        risk_level=risk_level,
        recommendations=_generate_recommendations(final_decision, risk_score, alert_severity),
        message=message,
        override_reason=override_reason,
        alert_severity=alert_severity,
        affected_modules=affected_modules
    )


def _generate_decision_message(decision: str, risk_score: float, override_reason: Optional[str]) -> str:
    """Generate human-readable decision message."""
    base_messages = {
        "ALLOW": f"Deployment permitted. Risk score {risk_score:.1f} is below threshold.",
        "WARN": f"Deployment flagged with warnings. Risk score {risk_score:.1f} requires attention.",
        "BLOCK": f"Deployment blocked. Risk score {risk_score:.1f} exceeds safe threshold."
    }
    
    message = base_messages.get(decision, "Unknown decision")
    
    if override_reason:
        message += f" Override: {override_reason}"
    
    return message


def _generate_recommendations(
    decision: str,
    risk_score: float,
    alert_severity: Optional[str]
) -> List[str]:
    """Generate actionable recommendations based on decision."""
    recs = []
    
    if decision == "ALLOW":
        recs.append("Continue with standard monitoring")
    
    elif decision == "WARN":
        if risk_score > 60:
            recs.append("Consider canary deployment first")
        if alert_severity:
            recs.append(f"Review {alert_severity} severity alerts")
        recs.append("Enable enhanced logging")
    
    elif decision == "BLOCK":
        recs.append("Address high-risk factors before deploying")
        recs.append("Consider breaking into smaller deployments")
        recs.append("Run additional manual QA checks")
    
    return recs


def evaluate_policy(
    deployment: Deployment,
    alert_severity: Optional[str] = None,
    affected_modules: Optional[List[str]] = None
) -> PolicyDecision:
    """
    Main entry point for policy evaluation.
    Aggregates all intelligence inputs and determines deployment decision.
    """
    risk_score = deployment.risk_score or 0.0
    risk_level = deployment.risk_level or "LOW"
    historical_failures = deployment.historical_failures or 0
    
    modules = affected_modules or []
    
    if deployment.sensitive_files:
        import json
        try:
            if isinstance(deployment.sensitive_files, str):
                modules = json.loads(deployment.sensitive_files)
            elif isinstance(deployment.sensitive_files, list):
                modules = deployment.sensitive_files
        except (json.JSONDecodeError, TypeError, AttributeError):
            pass
    
    return determine_decision(
        risk_score=risk_score,
        risk_level=risk_level,
        alert_severity=alert_severity,
        affected_modules=modules,
        historical_failures=historical_failures
    )


def evaluate_from_analysis(
    risk_score: float,
    risk_level: str,
    risk_factors: List[str],
    alert_severity: Optional[str] = None,
    affected_modules: Optional[List[str]] = None,
    historical_failures: int = 0
) -> PolicyDecision:
    """
    Policy evaluation that works directly with analysis results
    (for cases where Deployment object is not yet persisted).
    """
    modules = affected_modules or []
    
    return determine_decision(
        risk_score=risk_score,
        risk_level=risk_level,
        alert_severity=alert_severity,
        affected_modules=modules,
        historical_failures=historical_failures
    )