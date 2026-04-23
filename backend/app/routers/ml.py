import os
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from ..database import get_db
from ..services.ml_engine import ml_engine
from ..services.analytics_engine import get_ml_performance_metrics

router = APIRouter(prefix="/api/ml", tags=["machine_learning"])

def verify_ml_admin_token(x_api_key: str = Header(None)):
    token = os.getenv("ML_ADMIN_TOKEN", "supersecret")
    if not x_api_key or x_api_key != token:
        raise HTTPException(status_code=401, detail="Invalid or missing ML Admin token")
    return x_api_key

@router.post("/train")
def train_prediction_model(
    db: Session = Depends(get_db),
    admin_token: str = Depends(verify_ml_admin_token)
):
    """
    Manually triggers the ML training pipeline using historical data.
    Requires successful and failed deployments to build balanced context.
    """
    result = ml_engine.train_model(db)
    
    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result.get("message"))
        
    return result

@router.get("/metrics")
def get_metrics(
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    Real-time telemetry indicating ML predicting performance.
    """
    return get_ml_performance_metrics(db, limit)
