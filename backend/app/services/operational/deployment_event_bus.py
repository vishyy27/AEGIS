import logging
from typing import Dict, Any
from .event_router import event_router

logger = logging.getLogger("aegis.operational.deployment")

class DeploymentEventBus:
    """
    Handles deployment synchronization and operational memory indexing.
    """
    async def publish_deployment_state(self, deployment: dict):
        # We can implement Redis pub/sub here for scalability
        await event_router.route_deployment(deployment)

deployment_event_bus = DeploymentEventBus()
