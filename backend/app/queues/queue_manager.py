"""
Phase 11.7.10: Queue manager for operational events.

Provides a centralized interface for submitting events to background workers.
"""

import logging
from typing import Dict, Any
from ..workers.event_worker import telemetry_worker, persistence_worker

logger = logging.getLogger("aegis.queues")


class QueueManager:
    """Facade for submitting events to the appropriate background worker."""

    async def submit_telemetry(self, event: Dict[str, Any]):
        await telemetry_worker.submit(event)

    async def submit_for_persistence(self, event: Dict[str, Any]):
        await persistence_worker.submit(event)

    @property
    def stats(self) -> Dict[str, int]:
        return {
            "telemetry_pending": telemetry_worker.pending,
            "persistence_pending": persistence_worker.pending,
        }


queue_manager = QueueManager()
