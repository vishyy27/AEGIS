from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .database import engine, Base

# Create DB tables
Base.metadata.create_all(bind=engine)

# Create performance indexes for Phase 5 alert intelligence
from sqlalchemy import text
with engine.connect() as conn:
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_deployments_repo_timestamp ON deployments(repo_name, timestamp DESC)",
        "CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON alerts(timestamp)",
        "CREATE INDEX IF NOT EXISTS idx_alerts_affected_service ON alerts(affected_service)",
    ]
    for idx in indexes:
        try:
            conn.execute(text(idx))
        except Exception:
            pass
    conn.commit()

app = FastAPI(title=settings.PROJECT_NAME)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ROOT (fixes your 404 confusion)
@app.get("/")
def root():
    return {"message": "Backend is running 🚀"}


# Health check
@app.get("/api/health")
def read_health():
    return {"status": "healthy"}


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
