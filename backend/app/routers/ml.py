from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..services.ml_engine import ml_engine

router = APIRouter(prefix="/api/ml", tags=["machine_learning"])

@router.post("/train")
def train_prediction_model(db: Session = Depends(get_db)):
    """
    Manually triggers the ML training pipeline using historical data.
    Requires successful and failed deployments to build balanced context.
    """
    result = ml_engine.train_model(db)
    
    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result.get("message"))
        
    return result
