"""
Phase 11.2: WebSocket Connection Manager.

Manages WebSocket connections for real-time telemetry streaming.
Supports:
  - Connection lifecycle management (connect/disconnect)
  - Topic-based subscriptions (deployments, alerts, telemetry, incidents)
  - Broadcast to all subscribers of a topic
  - Per-connection message delivery
  - Heartbeat keepalive
  
Architecture:
  - Stateless-safe: Connection state is in-memory per process instance.
    For multi-process deployments, use Redis pub/sub (future extension).
  - Async-safe: All operations use asyncio primitives.
"""

import asyncio
import json
import logging
from typing import Dict, Set, Optional, Any
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger("aegis.websocket")


class ConnectionManager:
    """Manages WebSocket connections with topic-based subscriptions."""

    def __init__(self):
        # connection_id → WebSocket
        self._connections: Dict[str, WebSocket] = {}
        # topic → set of connection_ids
        self._subscriptions: Dict[str, Set[str]] = {}
        # connection_id → set of topics
        self._connection_topics: Dict[str, Set[str]] = {}
        self._lock = asyncio.Lock()
        self._counter = 0

    async def connect(self, websocket: WebSocket, org_id: str, topics: Optional[list] = None) -> str:
        """Accept a WebSocket connection, scope to organization, and subscribe to topics."""
        await websocket.accept()
        
        async with self._lock:
            self._counter += 1
            connection_id = f"ws-{self._counter}-{int(datetime.utcnow().timestamp())}"
            self._connections[connection_id] = websocket
            self._connection_topics[connection_id] = set()

            # Subscribe to requested topics (scoped to organization)
            sub_topics = topics or ["deployments", "alerts", "telemetry", "incidents", "policy"]
            for topic in sub_topics:
                # Scoped topic: org:{org_id}:{topic}
                scoped_topic = f"org:{org_id}:{topic}"
                if scoped_topic not in self._subscriptions:
                    self._subscriptions[scoped_topic] = set()
                self._subscriptions[scoped_topic].add(connection_id)
                self._connection_topics[connection_id].add(scoped_topic)

        logger.info(
            f"[WS] connected id={connection_id} org={org_id} topics={sub_topics} "
            f"total_connections={len(self._connections)}"
        )
        
        # Send welcome message
        await self.send_personal(connection_id, {
            "type": "connection_established",
            "connection_id": connection_id,
            "organization_id": org_id,
            "subscribed_topics": sub_topics,
            "timestamp": datetime.utcnow().isoformat(),
        })
        
        return connection_id

    async def disconnect(self, connection_id: str):
        """Remove a WebSocket connection and clean up subscriptions."""
        async with self._lock:
            # Remove from all topic subscriptions
            topics = self._connection_topics.pop(connection_id, set())
            for scoped_topic in topics:
                if scoped_topic in self._subscriptions:
                    self._subscriptions[scoped_topic].discard(connection_id)
                    if not self._subscriptions[scoped_topic]:
                        del self._subscriptions[scoped_topic]
            
            self._connections.pop(connection_id, None)

        logger.info(
            f"[WS] disconnected id={connection_id} "
            f"total_connections={len(self._connections)}"
        )

    async def send_personal(self, connection_id: str, message: dict):
        """Send a message to a specific connection."""
        ws = self._connections.get(connection_id)
        if ws:
            try:
                await ws.send_json(message)
            except Exception as e:
                logger.warning(f"[WS] send_failed id={connection_id} error={e}")
                await self.disconnect(connection_id)

    async def broadcast_to_topic(self, topic: str, message: dict, org_id: Optional[str] = None):
        """Broadcast a message to subscribers. If org_id provided, scopes to that tenant."""
        # Determine scoped topic name
        scoped_topic = f"org:{org_id}:{topic}" if org_id else topic
        
        subscribers = self._subscriptions.get(scoped_topic, set()).copy()
        if not subscribers:
            return

        message["_topic"] = topic  # Keep original topic in payload for frontend
        message["_scoped_topic"] = scoped_topic
        message["_broadcast_at"] = datetime.utcnow().isoformat()
        if org_id:
            message["_organization_id"] = org_id

        disconnected = []
        for conn_id in subscribers:
            ws = self._connections.get(conn_id)
            if ws:
                try:
                    await ws.send_json(message)
                except Exception:
                    disconnected.append(conn_id)

        # Clean up dead connections
        for conn_id in disconnected:
            await self.disconnect(conn_id)

        if disconnected:
            logger.info(
                f"[WS] broadcast topic={scoped_topic} delivered={len(subscribers) - len(disconnected)} "
                f"dropped={len(disconnected)}"
            )

    async def broadcast_all(self, message: dict):
        """Broadcast a message to ALL connected clients regardless of topic."""
        all_connections = list(self._connections.keys())
        disconnected = []
        
        message["_broadcast_at"] = datetime.utcnow().isoformat()

        for conn_id in all_connections:
            ws = self._connections.get(conn_id)
            if ws:
                try:
                    await ws.send_json(message)
                except Exception:
                    disconnected.append(conn_id)

        for conn_id in disconnected:
            await self.disconnect(conn_id)

    @property
    def active_connections(self) -> int:
        return len(self._connections)

    @property
    def topic_stats(self) -> Dict[str, int]:
        return {topic: len(subs) for topic, subs in self._subscriptions.items()}

    async def subscribe(self, connection_id: str, topic: str):
        """Subscribe an existing connection to an additional topic."""
        async with self._lock:
            if connection_id not in self._connections:
                return
            if topic not in self._subscriptions:
                self._subscriptions[topic] = set()
            self._subscriptions[topic].add(connection_id)
            self._connection_topics[connection_id].add(topic)

    async def unsubscribe(self, connection_id: str, topic: str):
        """Unsubscribe a connection from a topic."""
        async with self._lock:
            if topic in self._subscriptions:
                self._subscriptions[topic].discard(connection_id)
            if connection_id in self._connection_topics:
                self._connection_topics[connection_id].discard(topic)


# Singleton instance
ws_manager = ConnectionManager()
