import logging
from typing import Dict, Any
from .event_router import event_router

logger = logging.getLogger("aegis.operational.anomaly")

class AnomalyPipeline:
    """
    Handles anomaly propagation and correlation sync.
    """
    async def process_anomaly(self, anomaly: dict):
        await event_router.route_anomaly(anomaly)

anomaly_pipeline = AnomalyPipeline()
