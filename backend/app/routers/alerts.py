import json
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.alerts import Alert
from ..schemas.alert_schema import AlertResponse, IncidentPatternResponse, IncidentSummaryResponse

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


def _parse_incident_pattern(raw: str | None) -> dict | None:
    if not raw:
        return None
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return None


@router.get("/", response_model=List[AlertResponse])
def get_alerts(db: Session = Depends(get_db)):
    alerts = db.query(Alert).order_by(Alert.timestamp.desc()).all()
    response = []
    for a in alerts:
        response.append(
            AlertResponse(
                id=a.id,
                deployment_id=a.deployment_id,
                alert_type=a.alert_type,
                severity=a.severity,
                message=a.message,
                incident_pattern=_parse_incident_pattern(a.incident_pattern),
                affected_service=a.affected_service,
                status=a.status,
                timestamp=a.timestamp,
            )
        )
    return response


@router.get("/{alert_id}", response_model=AlertResponse)
def get_alert(alert_id: int, db: Session = Depends(get_db)):
    a = db.query(Alert).filter(Alert.id == alert_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="Alert not found")
    return AlertResponse(
        id=a.id,
        deployment_id=a.deployment_id,
        alert_type=a.alert_type,
        severity=a.severity,
        message=a.message,
        incident_pattern=_parse_incident_pattern(a.incident_pattern),
        affected_service=a.affected_service,
        status=a.status,
        timestamp=a.timestamp,
    )


@router.get("/incidents", response_model=IncidentSummaryResponse)
def get_incidents(db: Session = Depends(get_db)):
    alerts = (
        db.query(Alert)
        .filter(Alert.incident_pattern.isnot(None))
        .order_by(Alert.timestamp.desc())
        .all()
    )

    pattern_groups: Dict[str, Dict[str, Any]] = {}

    for alert in alerts:
        parsed = _parse_incident_pattern(alert.incident_pattern)
        if not parsed:
            continue

        patterns = parsed if isinstance(parsed, list) else [parsed]

        for pattern in patterns:
            if not isinstance(pattern, dict):
                continue

            ptype = pattern.get("type", "unknown")
            severity = pattern.get("severity", "LOW")

            if ptype not in pattern_groups:
                pattern_groups[ptype] = {
                    "incident_pattern": ptype.replace("_", " ").title(),
                    "severity": severity,
                    "count": 0,
                    "last_occurrence": alert.timestamp,
                }

            pattern_groups[ptype]["count"] += 1
            if alert.timestamp > pattern_groups[ptype]["last_occurrence"]:
                pattern_groups[ptype]["last_occurrence"] = alert.timestamp

    incidents = [
        IncidentPatternResponse(**v) for v in pattern_groups.values()
    ]
    incidents.sort(key=lambda x: x.count, reverse=True)

    return IncidentSummaryResponse(
        incidents=incidents,
        total_incidents=sum(i.count for i in incidents),
    )
