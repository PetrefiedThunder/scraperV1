"""
WebSocket manager for real-time scraping progress updates
"""

from typing import Dict, Set
from fastapi import WebSocket, WebSocketDisconnect
import json
import asyncio
from datetime import datetime


class ConnectionManager:
    """Manages WebSocket connections and broadcasts"""

    def __init__(self):
        # Map of result_id -> set of WebSocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # Global connections (receive all updates)
        self.global_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket, result_id: str = None):
        """Accept a new WebSocket connection"""
        await websocket.accept()

        if result_id:
            if result_id not in self.active_connections:
                self.active_connections[result_id] = set()
            self.active_connections[result_id].add(websocket)
        else:
            self.global_connections.add(websocket)

    def disconnect(self, websocket: WebSocket, result_id: str = None):
        """Remove a WebSocket connection"""
        if result_id and result_id in self.active_connections:
            self.active_connections[result_id].discard(websocket)
            if not self.active_connections[result_id]:
                del self.active_connections[result_id]
        else:
            self.global_connections.discard(websocket)

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send a message to a specific connection"""
        try:
            await websocket.send_json(message)
        except Exception:
            pass

    async def broadcast_to_result(self, result_id: str, message: dict):
        """Broadcast a message to all connections watching a specific result"""
        if result_id not in self.active_connections:
            return

        disconnected = set()
        for connection in self.active_connections[result_id]:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.add(connection)

        # Clean up disconnected clients
        for connection in disconnected:
            self.disconnect(connection, result_id)

    async def broadcast_global(self, message: dict):
        """Broadcast a message to all global connections"""
        disconnected = set()
        for connection in self.global_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.add(connection)

        # Clean up disconnected clients
        for connection in disconnected:
            self.disconnect(connection)

    async def send_progress_update(
        self,
        result_id: str,
        status: str,
        progress: float = None,
        items_scraped: int = None,
        pages_scraped: int = None,
        current_url: str = None,
        message: str = None,
    ):
        """Send a progress update for a scraping job"""
        update = {
            "type": "progress",
            "result_id": result_id,
            "status": status,
            "timestamp": datetime.utcnow().isoformat(),
        }

        if progress is not None:
            update["progress"] = progress
        if items_scraped is not None:
            update["items_scraped"] = items_scraped
        if pages_scraped is not None:
            update["pages_scraped"] = pages_scraped
        if current_url is not None:
            update["current_url"] = current_url
        if message is not None:
            update["message"] = message

        await self.broadcast_to_result(result_id, update)
        await self.broadcast_global(update)

    async def send_completion(
        self,
        result_id: str,
        status: str,
        total_items: int,
        total_pages: int,
        duration_seconds: float,
        error_message: str = None,
    ):
        """Send a completion notification"""
        update = {
            "type": "completion",
            "result_id": result_id,
            "status": status,
            "total_items": total_items,
            "total_pages": total_pages,
            "duration_seconds": duration_seconds,
            "timestamp": datetime.utcnow().isoformat(),
        }

        if error_message:
            update["error_message"] = error_message

        await self.broadcast_to_result(result_id, update)
        await self.broadcast_global(update)


# Global connection manager instance
manager = ConnectionManager()
