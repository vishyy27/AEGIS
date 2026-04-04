from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .database import engine, Base

# Create DB tables
Base.metadata.create_all(bind=engine)

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

app.include_router(dashboard_router)
app.include_router(deployments_router)
app.include_router(analysis_router)
app.include_router(integrations_router)
app.include_router(alerts_router)
app.include_router(settings_router)
app.include_router(environments_router)
app.include_router(insights_router)
app.include_router(incidents_router)
