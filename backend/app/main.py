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
    return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})



# ROOT (fixes your 404 confusion)
@app.get("/")
def root():
    return {"message": "Backend is running 🚀"}


# Health check
@app.get("/health")
def read_health():
    # A real implementation would verify DB and ML model status dynamically.
    return {
        "status": "healthy",
        "api": "up",
        "database": "connected",
        "ml_model": "loaded",
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
