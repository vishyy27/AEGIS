"""Phase 11: WebSocket router for real-time telemetry streaming."""

import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from typing import Optional, List

from ..services.websocket_manager import ws_manager
from ..services.event_stream_service import event_stream
from ..database import get_db

logger = logging.getLogger("aegis.ws.router")
router = APIRouter(tags=["websocket"])


@router.websocket("/ws/telemetry")
async def telemetry_websocket(
    websocket: WebSocket,
    topics: Optional[str] = Query(None),
):
    """WebSocket endpoint for real-time telemetry streaming."""
    topic_list = topics.split(",") if topics else None
    connection_id = await ws_manager.connect(websocket, topic_list)

    try:
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                msg_type = msg.get("type")

                if msg_type == "subscribe":
                    topic = msg.get("topic")
                    if topic:
                        await ws_manager.subscribe(connection_id, topic)
                        await ws_manager.send_personal(connection_id, {
                            "type": "subscribed", "topic": topic
                        })

                elif msg_type == "unsubscribe":
                    topic = msg.get("topic")
                    if topic:
                        await ws_manager.unsubscribe(connection_id, topic)
                        await ws_manager.send_personal(connection_id, {
                            "type": "unsubscribed", "topic": topic
                        })

                elif msg_type == "ping":
                    await ws_manager.send_personal(connection_id, {"type": "pong"})

            except json.JSONDecodeError:
                await ws_manager.send_personal(connection_id, {
                    "type": "error", "message": "Invalid JSON"
                })

    except WebSocketDisconnect:
        await ws_manager.disconnect(connection_id)


@router.get("/api/telemetry/status")
def get_telemetry_status():
    """Get current WebSocket telemetry status."""
    return {
        "active_connections": ws_manager.active_connections,
        "topic_stats": ws_manager.topic_stats,
    }


@router.get("/api/telemetry/events")
def get_recent_events(limit: int = 50, event_type: Optional[str] = None, db=Depends(get_db)):
    """Get recent deployment events for initial load."""
    event_types = [event_type] if event_type else None
    return event_stream.get_recent_events(db, limit=limit, event_types=event_types)
