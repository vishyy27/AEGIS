from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..models.deployment import Deployment
from ..schemas.deployment_schema import DeploymentCreate, DeploymentResponse

router = APIRouter(prefix="/api/deployments", tags=["deployments"])


@router.get("/", response_model=List[DeploymentResponse])
def list_deployments(skip: int = 0, limit: int = 100, search: str = None, db: Session = Depends(get_db)):
    query = db.query(Deployment)
    if search:
        search_term = f"%{search}%"
        from sqlalchemy import or_
        query = query.filter(
            or_(
                Deployment.service.ilike(search_term),
                Deployment.repo_name.ilike(search_term),
                Deployment.commit_hash.ilike(search_term)
            )
        )
    deployments = query.offset(skip).limit(limit).all()
    return deployments


@router.get("/{deployment_id}", response_model=DeploymentResponse)
def get_deployment(deployment_id: int, db: Session = Depends(get_db)):
    deployment = db.query(Deployment).filter(Deployment.id == deployment_id).first()

    if deployment is None:
        raise HTTPException(status_code=404, detail="Deployment not found")

    return deployment


@router.post("/", response_model=DeploymentResponse)
def create_deployment(deployment_in: DeploymentCreate, db: Session = Depends(get_db)):
    db_deployment = Deployment(
        service=deployment_in.service,
        environment=deployment_in.environment,
        risk_score=25.0,
        status="pending",
    )

    db.add(db_deployment)
    db.commit()
    db.refresh(db_deployment)

    return db_deployment
