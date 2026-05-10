"""
Phase 11.7.10: Background event worker.

Processes queued operational events asynchronously.
Decouples event persistence from the hot request path.
"""

import asyncio
import logging
from typing import Dict, Any, Callable, Awaitable, List

logger = logging.getLogger("aegis.workers.event")


class EventWorker:
    """
    Simple async background worker that processes events from an internal queue.
    Production systems would use Celery/Redis queues; this provides the same
    interface for single-process deployments.
    """

    def __init__(self, name: str = "default", max_queue_size: int = 1000):
        self.name = name
        self._queue: asyncio.Queue = asyncio.Queue(maxsize=max_queue_size)
        self._handlers: Dict[str, Callable[[Dict[str, Any]], Awaitable[None]]] = {}
        self._task = None

    def register_handler(self, event_type: str, handler: Callable[[Dict[str, Any]], Awaitable[None]]):
        self._handlers[event_type] = handler

    def start(self):
        if self._task is None:
            self._task = asyncio.create_task(self._process_loop())
            logger.info(f"[Worker:{self.name}] started")

    async def submit(self, event: Dict[str, Any]):
        try:
            self._queue.put_nowait(event)
        except asyncio.QueueFull:
            logger.warning(f"[Worker:{self.name}] queue full, dropping event type={event.get('type')}")

    async def _process_loop(self):
        while True:
            event = await self._queue.get()
            event_type = event.get("type", "unknown")
            handler = self._handlers.get(event_type)
            if handler:
                try:
                    await handler(event)
                except Exception as e:
                    logger.error(f"[Worker:{self.name}] handler error type={event_type}: {e}")
            self._queue.task_done()

    @property
    def pending(self) -> int:
        return self._queue.qsize()


# Singleton workers
telemetry_worker = EventWorker(name="telemetry", max_queue_size=2000)
persistence_worker = EventWorker(name="persistence", max_queue_size=500)
