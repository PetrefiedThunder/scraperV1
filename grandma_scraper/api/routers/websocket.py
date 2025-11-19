"""
WebSocket endpoints for real-time updates
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from grandma_scraper.websockets.manager import manager
from grandma_scraper.auth.security import get_current_user_ws
from uuid import UUID
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["websocket"])


@router.websocket("/progress")
async def websocket_global_progress(websocket: WebSocket):
    """
    WebSocket endpoint for receiving all scraping progress updates

    Clients connect to this endpoint to receive real-time updates
    for all running scraping jobs.
    """
    await manager.connect(websocket)

    try:
        while True:
            # Keep connection alive and handle ping/pong
            data = await websocket.receive_text()

            # Echo back pings
            if data == "ping":
                await websocket.send_text("pong")

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("Global WebSocket client disconnected")


@router.websocket("/progress/{result_id}")
async def websocket_result_progress(websocket: WebSocket, result_id: str):
    """
    WebSocket endpoint for receiving progress updates for a specific result

    Clients connect to this endpoint to receive real-time updates
    for a specific scraping job execution.

    Args:
        result_id: The UUID of the scrape result to monitor
    """
    await manager.connect(websocket, result_id=result_id)

    try:
        while True:
            # Keep connection alive and handle ping/pong
            data = await websocket.receive_text()

            # Echo back pings
            if data == "ping":
                await websocket.send_text("pong")

    except WebSocketDisconnect:
        manager.disconnect(websocket, result_id=result_id)
        logger.info(f"WebSocket client disconnected from result {result_id}")
