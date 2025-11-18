"""
Result API schemas.

Pydantic models for result-related API responses.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID

from pydantic import BaseModel

from grandma_scraper.db.models import JobStatus


class ResultResponse(BaseModel):
    """Scrape result response."""

    id: UUID
    job_id: UUID
    run_id: UUID
    status: JobStatus
    items: List[Dict[str, Any]]
    total_items: int
    pages_scraped: int
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    duration_seconds: Optional[float]
    error_message: Optional[str]
    error_details: Optional[Dict[str, Any]]
    warnings: List[str]
    created_at: datetime

    class Config:
        from_attributes = True
