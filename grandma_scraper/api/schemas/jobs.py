"""
Job API schemas.

Pydantic models for job-related API requests and responses.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from grandma_scraper.core.models import ScrapeJob


class JobCreate(BaseModel):
    """Job creation request."""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    config: dict = Field(..., description="Full ScrapeJob configuration as dict")
    enabled: bool = True


class JobUpdate(BaseModel):
    """Job update request."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    config: Optional[dict] = None
    enabled: Optional[bool] = None


class JobResponse(BaseModel):
    """Job response."""

    id: UUID
    name: str
    description: Optional[str]
    config: dict
    enabled: bool
    owner_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
