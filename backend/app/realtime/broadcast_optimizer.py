"""
Phase 11.7.10: Backend realtime broadcast optimizer.

Provides batched WebSocket broadcast with configurable flush intervals.
Reduces per-event broadcast overhead under high-frequency telemetry load.
"""

import asyncio
import logging
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger("aegis.realtime.optimizer")


class BroadcastOptimizer:
    """
    Accumulates outbound WebSocket messages per topic and flushes them 
    in batched payloads on a configurable interval.
    """

    def __init__(self, flush_interval: float = 0.3):
        self.flush_interval = flush_interval
        self._queues: Dict[str, List[Dict[str, Any]]] = {}
        self._lock = asyncio.Lock()
        self._task = None
        self._broadcast_fn = None

    def start(self, broadcast_fn):
        """Start the flush loop. broadcast_fn(topic, payload) must be async."""
        self._broadcast_fn = broadcast_fn
        if self._task is None:
            self._task = asyncio.create_task(self._flush_loop())

    async def enqueue(self, topic: str, message: dict):
        async with self._lock:
            if topic not in self._queues:
                self._queues[topic] = []
            self._queues[topic].append(message)

    async def _flush_loop(self):
        while True:
            await asyncio.sleep(self.flush_interval)
            await self._flush()

    async def _flush(self):
        async with self._lock:
            queues_snapshot = dict(self._queues)
            self._queues = {}

        if not self._broadcast_fn:
            return

        for topic, messages in queues_snapshot.items():
            if not messages:
                continue

            if len(messages) == 1:
                await self._broadcast_fn(topic, messages[0])
            else:
                batch_payload = {
                    "type": "batch",
                    "topic": topic,
                    "events": messages,
                    "count": len(messages),
                    "timestamp": datetime.utcnow().isoformat(),
                }
                await self._broadcast_fn(topic, batch_payload)


broadcast_optimizer = BroadcastOptimizer(flush_interval=0.3)
