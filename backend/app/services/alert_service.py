from sqlalchemy.orm import Session
from ..models.alerts import Alert


def check_and_create_alert(
    db: Session, deployment_id: int, risk_score: float, historical_failures: int
) -> None:
    """
    Trigger alert if risk score > 70 or historical failures > 3.
    """
    if risk_score > 70 or historical_failures > 3:
        alert_type = "HIGH_RISK_DEPLOYMENT" if risk_score > 70 else "FREQUENT_FAILURES"
        severity = "CRITICAL" if risk_score > 70 else "WARNING"
        message = f"Important issue detected: {alert_type} (Score: {risk_score}, Failures: {historical_failures})"

        alert = Alert(
            deployment_id=deployment_id,
            alert_type=alert_type,
            severity=severity,
            message=message,
        )
        db.add(alert)
        db.commit()
