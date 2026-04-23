from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from ..database import get_db
from ..schemas.analysis_schema import AnalysisRequest, AnalysisResponse
from ..services.analysis_orchestrator import evaluate_deployment

router = APIRouter(prefix="/api/analysis", tags=["analysis"])


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_deployment(request: AnalysisRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    return evaluate_deployment(request, db, background_tasks)
