import logging
from typing import Dict, Any
from .telemetry_dispatcher import telemetry_dispatcher
from ..websocket_manager import ws_manager

logger = logging.getLogger("aegis.operational.router")

class OperationalEventRouter:
    """
    Centralized event router for operational intelligence pipeline.
    Routes events to stream batchers, websocket topics, and observability pipelines.
    """
    
    async def route_telemetry(self, service: str, data: dict):
        """Routes high-frequency telemetry through the dispatcher for batching."""
        await telemetry_dispatcher.push_telemetry(service, data)
        
    async def route_deployment(self, deployment: dict):
        """Routes a deployment update to the deployments stream directly."""
        await ws_manager.broadcast_to_topic("deployments", {
            "type": "deployment_update",
            "deployment": deployment
        })
        
    async def route_anomaly(self, anomaly: dict):
        """Routes detected anomalies immediately."""
        await ws_manager.broadcast_to_topic("alerts", {
            "type": "anomaly_detected",
            **anomaly
        })

    async def route_incident(self, incident: dict):
        """Routes policy violations and incidents immediately."""
        await ws_manager.broadcast_to_topic("policy", {
            "type": "policy_violation",
            **incident
        })

event_router = OperationalEventRouter()
