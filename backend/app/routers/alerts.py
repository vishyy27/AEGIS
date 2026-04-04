from fastapi import APIRouter, Depends
from typing import List
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.alerts import Alert
from ..schemas.alert_schema import AlertResponse

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


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
                timestamp=a.timestamp,
            )
        )
    return response


@router.get("/{id}", response_model=AlertResponse)
def get_alert(id: int, db: Session = Depends(get_db)):
    a = db.query(Alert).filter(Alert.id == id).first()
    if not a:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Alert not found")
    return AlertResponse(
        id=a.id,
        deployment_id=a.deployment_id,
        alert_type=a.alert_type,
        severity=a.severity,
        message=a.message,
        timestamp=a.timestamp,
    )
