import logging
from typing import Dict, Any
from .event_router import event_router

logger = logging.getLogger("aegis.operational.pipeline")

class OperationalEventPipeline:
    """
    Ingests raw events from the system, normalizes them, and passes them to the router.
    Acts as the main entrypoint for the operational intelligence platform's event propagation.
    """
    
    async def process_telemetry(self, service: str, cpu: float, memory: float, latency: float, errors: int):
        data = {
            "cpu": cpu,
            "memory": memory,
            "latency": latency,
            "errors": errors
        }
        await event_router.route_telemetry(service, data)
        
    async def process_deployment_state_change(self, db, deployment_id: int, new_status: str, risk_score: float = None):
        # We would typically fetch full details from DB here.
        # For optimization, we only send delta or full serialized object.
        deployment = {
            "id": deployment_id,
            "status": new_status
        }
        if risk_score is not None:
            deployment["risk_score"] = risk_score
            
        await event_router.route_deployment(deployment)

pipeline = OperationalEventPipeline()
