"""Phase 11: Deployment Replay, Simulation, AI Assistant, Fleet, RBAC routers."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any, List

from ..database import get_db
from ..services.deployment_replay_service import replay_service
from ..services.simulation_engine import simulation_engine
from ..services.ai_assistant_service import ai_assistant
from ..services.fleet_intelligence import fleet_intelligence
from ..services.incident_intelligence import incident_intelligence
from ..services.rbac_service import rbac_service

# --- Replay Router ---
replay_router = APIRouter(prefix="/api/replay", tags=["replay"])

@replay_router.get("/list")
def list_replays(service: Optional[str] = None, limit: int = 20, db: Session = Depends(get_db)):
    return replay_service.get_replay_list(db, service=service, limit=limit)

@replay_router.get("/timeline/{deployment_id}")
def get_timeline(deployment_id: int, db: Session = Depends(get_db)):
    result = replay_service.get_replay_timeline(db, deployment_id)
    if not result:
        raise HTTPException(status_code=404, detail="Deployment not found")
    return result


# --- Simulation Router ---
simulation_router = APIRouter(prefix="/api/simulation", tags=["simulation"])

class SimulationRequest(BaseModel):
    simulation_name: Optional[str] = None
    repo_name: str = "simulation/test-repo"
    commit_count: int = 5
    files_changed: int = 10
    code_churn: int = 200
    test_coverage: float = 80.0
    dependency_updates: int = 0
    historical_failures: int = 0
    deployment_frequency: int = 3
    churn_ratio: float = 0.5
    commit_density: float = 2.0
    failure_rate_last_10: float = 0.0
    avg_risk_last_5: float = 30.0
    has_db_migration: bool = False
    has_auth_changes: bool = False
    has_payment_changes: bool = False
    has_core_module_changes: bool = False
    sensitive_files: List[str] = []

@simulation_router.post("/run")
def run_simulation(request: SimulationRequest, db: Session = Depends(get_db)):
    return simulation_engine.run_simulation(db, request.model_dump())

@simulation_router.get("/history")
def simulation_history(limit: int = 20, db: Session = Depends(get_db)):
    return simulation_engine.get_simulation_history(db, limit=limit)

@simulation_router.get("/presets")
def simulation_presets():
    return simulation_engine.get_presets()


# --- AI Assistant Router ---
assistant_router = APIRouter(prefix="/api/assistant", tags=["assistant"])

class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    message: str

@assistant_router.post("/chat")
def chat(request: ChatRequest, db: Session = Depends(get_db)):
    return ai_assistant.chat(db, request.session_id, request.message)

@assistant_router.get("/sessions")
def get_sessions(limit: int = 20, db: Session = Depends(get_db)):
    return ai_assistant.get_sessions(db, limit=limit)

@assistant_router.get("/sessions/{session_id}/messages")
def get_messages(session_id: str, db: Session = Depends(get_db)):
    return ai_assistant.get_session_messages(db, session_id)


# --- Fleet Intelligence Router ---
fleet_router = APIRouter(prefix="/api/fleet", tags=["fleet"])

@fleet_router.get("/overview")
def fleet_overview(db: Session = Depends(get_db)):
    return fleet_intelligence.get_fleet_overview(db)

@fleet_router.get("/services")
def fleet_services(db: Session = Depends(get_db)):
    return fleet_intelligence.get_service_profiles(db)

@fleet_router.get("/heatmap")
def fleet_heatmap(days: int = 7, db: Session = Depends(get_db)):
    return fleet_intelligence.get_risk_heatmap(db, days=days)

@fleet_router.get("/ranking")
def fleet_ranking(sort_by: str = "risk", db: Session = Depends(get_db)):
    return fleet_intelligence.get_service_ranking(db, sort_by=sort_by)


# --- Incident Intelligence Router ---
incident_router = APIRouter(prefix="/api/incidents", tags=["incidents"])

@incident_router.get("/detect")
def detect_incidents(lookback_hours: int = 24, db: Session = Depends(get_db)):
    return incident_intelligence.detect_incidents(db, lookback_hours=lookback_hours)

@incident_router.get("/list")
def list_incidents(status: Optional[str] = None, severity: Optional[str] = None, limit: int = 20, db: Session = Depends(get_db)):
    return incident_intelligence.get_incidents(db, status=status, severity=severity, limit=limit)

@incident_router.get("/{incident_id}")
def get_incident(incident_id: str, db: Session = Depends(get_db)):
    result = incident_intelligence.get_incident_detail(db, incident_id)
    if not result:
        raise HTTPException(status_code=404, detail="Incident not found")
    return result

class ResolveRequest(BaseModel):
    root_cause: Optional[str] = None

@incident_router.post("/{incident_id}/resolve")
def resolve_incident(incident_id: str, request: ResolveRequest, db: Session = Depends(get_db)):
    success = incident_intelligence.resolve_incident(db, incident_id, request.root_cause)
    if not success:
        raise HTTPException(status_code=404, detail="Incident not found")
    return {"status": "resolved", "incident_id": incident_id}


# --- RBAC / Audit Router ---
audit_router = APIRouter(prefix="/api/audit", tags=["audit"])

@audit_router.get("/trail")
def audit_trail(limit: int = 50, action: Optional[str] = None, db: Session = Depends(get_db)):
    return rbac_service.get_audit_trail(db, limit=limit, action=action)
