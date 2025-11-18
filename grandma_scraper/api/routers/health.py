"""
Health check endpoints.

Provides system health and status information.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from grandma_scraper import __version__
from grandma_scraper.db import get_db


router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    version: str
    database: str


@router.get("/health", response_model=HealthResponse)
async def health_check(db: Session = Depends(get_db)) -> HealthResponse:
    """
    Health check endpoint.

    Returns system status and version information.

    Returns:
        Health status response
    """
    # Check database connection
    try:
        db.execute("SELECT 1")
        db_status = "ok"
    except Exception:
        db_status = "error"

    return HealthResponse(
        status="ok",
        version=__version__,
        database=db_status,
    )
