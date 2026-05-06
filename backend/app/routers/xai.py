"""Phase 11: XAI / Explainability API router."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from ..database import get_db
from ..models.deployment import Deployment
from ..services.xai_engine import xai_engine

router = APIRouter(prefix="/api/xai", tags=["xai"])


@router.get("/explanation/{deployment_id}")
def get_explanation(deployment_id: int, db: Session = Depends(get_db)):
    """Get full XAI explanation for a deployment."""
    deployment = db.query(Deployment).filter(Deployment.id == deployment_id).first()
    if not deployment:
        raise HTTPException(status_code=404, detail="Deployment not found")
    return xai_engine.generate_full_explanation(deployment, db)


@router.get("/waterfall/{deployment_id}")
def get_waterfall(deployment_id: int, db: Session = Depends(get_db)):
    """Get policy waterfall for a deployment."""
    deployment = db.query(Deployment).filter(Deployment.id == deployment_id).first()
    if not deployment:
        raise HTTPException(status_code=404, detail="Deployment not found")
    return xai_engine.generate_policy_waterfall(deployment, db)


@router.get("/confidence/{deployment_id}")
def get_confidence(deployment_id: int, db: Session = Depends(get_db)):
    """Get confidence breakdown for a deployment."""
    deployment = db.query(Deployment).filter(Deployment.id == deployment_id).first()
    if not deployment:
        raise HTTPException(status_code=404, detail="Deployment not found")
    return xai_engine.generate_confidence_breakdown(deployment, db)


@router.get("/feature-impacts/{deployment_id}")
def get_feature_impacts(deployment_id: int, db: Session = Depends(get_db)):
    """Get feature impact analysis for a deployment."""
    deployment = db.query(Deployment).filter(Deployment.id == deployment_id).first()
    if not deployment:
        raise HTTPException(status_code=404, detail="Deployment not found")
    return xai_engine.generate_feature_impacts(deployment)
