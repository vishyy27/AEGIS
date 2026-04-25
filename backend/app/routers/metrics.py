from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import functools
from datetime import datetime, timedelta

from ..database import get_db
from ..services.metrics_service import get_system_health, get_decision_intelligence_metrics

router = APIRouter(prefix="/api/metrics", tags=["metrics"])

# Simple cache dictionary for LRU caching
_cache = {}

def get_cached_metrics(func, db: Session, ttl_seconds: int = 60):
    cache_key = func.__name__
    now = datetime.utcnow()
    
    if cache_key in _cache:
        cached_time, cached_data = _cache[cache_key]
        if (now - cached_time).total_seconds() < ttl_seconds:
            return cached_data
            
    data = func(db)
    _cache[cache_key] = (now, data)
    return data

@router.get("/decision-intelligence")
def read_decision_intelligence(db: Session = Depends(get_db)):
    """GET decision intelligence aggregated metrics with 60s TTL cache."""
    return get_cached_metrics(get_decision_intelligence_metrics, db, ttl_seconds=60)

@router.get("/system-health")
def read_system_health(db: Session = Depends(get_db)):
    """GET lightweight intelligence system health check."""
    return get_cached_metrics(get_system_health, db, ttl_seconds=10)
