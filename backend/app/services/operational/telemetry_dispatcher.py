import asyncio
import logging
from typing import Dict, Any
from datetime import datetime
from ..websocket_manager import ws_manager

logger = logging.getLogger("aegis.telemetry.dispatcher")

class TelemetryDispatcher:
    """
    High-frequency stream batching for telemetry events.
    Batches rapid telemetry events and flushes them periodically to avoid WebSocket flood.
    """
    def __init__(self, flush_interval: float = 0.5):
        self.flush_interval = flush_interval
        self._batch: Dict[str, Any] = {}
        self._lock = asyncio.Lock()
        self._task = None

    def start(self):
        if self._task is None:
            self._task = asyncio.create_task(self._flush_loop())

    async def _flush_loop(self):
        while True:
            await asyncio.sleep(self.flush_interval)
            await self.flush()

    async def push_telemetry(self, service: str, data: dict):
        async with self._lock:
            # Overwrite with latest telemetry for the service in the current batch
            data['service'] = service
            data['timestamp'] = datetime.utcnow().isoformat()
            self._batch[service] = data

    async def flush(self):
        async with self._lock:
            if not self._batch:
                return
            
            payload = {
                "type": "telemetry_batch",
                "updates": self._batch,
                "timestamp": datetime.utcnow().isoformat()
            }
            self._batch = {}

        await ws_manager.broadcast_to_topic("telemetry", payload)


telemetry_dispatcher = TelemetryDispatcher(flush_interval=0.5)
