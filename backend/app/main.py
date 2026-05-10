from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time
import logging
from pythonjsonlogger import jsonlogger
from .config import settings
from .database import engine, Base

# Set up JSON structured logging
logger = logging.getLogger()
logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter('%(timestamp)s %(levelname)s %(name)s %(message)s')
logHandler.setFormatter(formatter)
logger.addHandler(logHandler)
logger.setLevel(settings.LOG_LEVEL)


# Create DB tables
Base.metadata.create_all(bind=engine)

# Create performance indexes for Phase 5 alert intelligence
from sqlalchemy import text
with engine.connect() as conn:
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_deployments_repo_timestamp ON deployments(repo_name, timestamp DESC)",
        "CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON alerts(timestamp)",
        "CREATE INDEX IF NOT EXISTS idx_alerts_affected_service ON alerts(affected_service)",
        "CREATE INDEX IF NOT EXISTS idx_deployment_events_dep_id ON deployment_events(deployment_id)",
        "CREATE INDEX IF NOT EXISTS idx_deployment_events_timestamp ON deployment_events(timestamp DESC)",
        "CREATE INDEX IF NOT EXISTS idx_anomaly_events_timestamp ON anomaly_events(timestamp DESC)",
        "CREATE INDEX IF NOT EXISTS idx_anomaly_events_service ON anomaly_events(service_name)",
    ]
    for idx in indexes:
        try:
            conn.execute(text(idx))
        except Exception:
            pass
    conn.commit()

from contextlib import asynccontextmanager
from .services.operational.telemetry_dispatcher import telemetry_dispatcher
from .realtime.broadcast_optimizer import broadcast_optimizer
from .workers.event_worker import telemetry_worker, persistence_worker
from .services.websocket_manager import ws_manager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start telemetry batching dispatcher
    telemetry_dispatcher.start()
    # Start broadcast optimizer
    broadcast_optimizer.start(ws_manager.broadcast_to_topic)
    # Start background workers
    telemetry_worker.start()
    persistence_worker.start()
    yield
    # Cleanup logic can go here

app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Phase 11.8.1: Tenant Resolution Middleware
from .middleware.tenant import TenantMiddleware
app.add_middleware(TenantMiddleware)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        logger.info(
            "API Request Processed",
            extra={
                "method": request.method,
                "url": str(request.url),
                "status_code": response.status_code,
                "latency_s": round(process_time, 4)
            }
        )
        return response
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(
            "API Request Failed",
            extra={
                "method": request.method,
                "url": str(request.url),
                "error": str(e),
                "latency_s": round(process_time, 4)
            },
            exc_info=True
        )
        raise

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled Exception", extra={"url": str(request.url), "error": str(exc)}, exc_info=True)
    return JSONResponse(
        status_code=500, 
        content={
            "detail": "Internal Server Error",
            "fallback_message": "The system encountered an unexpected condition. Please try again.",
            "error_type": type(exc).__name__
        }
    )



# ROOT (fixes your 404 confusion)
@app.get("/")
def root():
    return {"message": "Backend is running 🚀"}


# Health check
@app.get("/health")
def read_health():
    from .database import engine
    from sqlalchemy import text
    from .services.ml_engine import ml_engine

    db_status = "disconnected"
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            db_status = "connected"
    except Exception as e:
        logger.error(f"Health check DB error: {str(e)}")

    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "api": "up",
        "database": db_status,
        "ml_model": "loaded" if ml_engine.model else "not_loaded",
        "ml_model_version": ml_engine.current_version,
        "version": "1.0.0",
    }


# Routers
from .routers import (
    dashboard_router,
    deployments_router,
    analysis_router,
    integrations_router,
    alerts_router,
    settings_router,
    environments_router,
    insights_router,
)
from .routers.incidents import router as incidents_router
from .routers.ml import router as ml_router
from .routers.metrics import router as metrics_router

app.include_router(dashboard_router)
app.include_router(deployments_router)
app.include_router(analysis_router)
app.include_router(integrations_router)
app.include_router(alerts_router)
app.include_router(settings_router)
app.include_router(environments_router)
app.include_router(insights_router)
app.include_router(incidents_router)
app.include_router(ml_router)
app.include_router(metrics_router)

# Phase 11: AI-Native Real-Time DevOps Platform
from .routers.websocket import router as websocket_router
from .routers.xai import router as xai_router
from .routers.phase11_routes import (
    replay_router, simulation_router, assistant_router,
    fleet_router, incident_router as phase11_incident_router, audit_router,
)

app.include_router(websocket_router)
app.include_router(xai_router)
app.include_router(replay_router)
app.include_router(simulation_router)
app.include_router(assistant_router)
app.include_router(fleet_router)
app.include_router(phase11_incident_router)
app.include_router(audit_router)

# Phase 11.8.1: Enterprise Multi-Tenant Organization
from .routers.organizations import router as organizations_router
app.include_router(organizations_router)

# Phase 11.8.2: Advanced RBAC
from .routers.rbac import router as rbac_router
app.include_router(rbac_router)

# Bootstrap default organization and RBAC on startup
from .database import SessionLocal
from .services.organization_service import organization_service
from .services.advanced_rbac_service import rbac_service
from .middleware.tenant import DEFAULT_ORG_ID
try:
    _db = SessionLocal()
    # 1. Bootstrap system permissions & templates
    rbac_service.bootstrap_system_roles(_db)
    
    # 2. Ensure default org exists
    organization_service.ensure_default_organization(_db, DEFAULT_ORG_ID)
    _db.close()
except Exception as _e:
    logger.warning(f"Bootstrap skipped or failed: {_e}")

