"""
Authentication and user schemas for API.

Pydantic models for request/response validation.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from grandma_scraper.db.models import UserRole


class Token(BaseModel):
    """JWT token response."""

    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Data extracted from JWT token."""

    user_id: UUID


class UserBase(BaseModel):
    """Base user fields."""

    email: EmailStr
    username: str = Field(..., min_length=1, max_length=100)


class UserCreate(UserBase):
    """User creation request."""

    password: str = Field(..., min_length=8, max_length=72)


class UserUpdate(BaseModel):
    """User update request."""

    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=1, max_length=100)
    password: Optional[str] = Field(None, min_length=8, max_length=72)
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    """User response (safe for API responses)."""

    id: UUID
    is_active: bool
    is_superuser: bool
    role: UserRole
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # Enable ORM mode for SQLAlchemy models
