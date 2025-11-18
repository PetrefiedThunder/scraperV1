"""
User management endpoints.

Handles user CRUD operations.
"""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from grandma_scraper.auth import (
    get_current_active_user,
    UserResponse,
    UserUpdate,
    get_password_hash,
)
from grandma_scraper.auth.security import require_admin
from grandma_scraper.db import get_db
from grandma_scraper.db.models import User


router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """
    Get current user information.

    Args:
        current_user: Authenticated user from token

    Returns:
        Current user data
    """
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> User:
    """
    Update current user information.

    Args:
        user_update: User update data
        current_user: Authenticated user
        db: Database session

    Returns:
        Updated user data

    Raises:
        HTTPException: If email already taken
    """
    # Check if email is being changed and if it's already taken
    if user_update.email and user_update.email != current_user.email:
        existing_user = db.query(User).filter(User.email == user_update.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

    # Update fields
    if user_update.email:
        current_user.email = user_update.email
    if user_update.username:
        current_user.username = user_update.username
    if user_update.password:
        current_user.hashed_password = get_password_hash(user_update.password)

    db.commit()
    db.refresh(current_user)

    return current_user


@router.get("/", response_model=List[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> List[User]:
    """
    List all users (admin only).

    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        current_user: Admin user
        db: Database session

    Returns:
        List of users
    """
    users = db.query(User).offset(skip).limit(limit).all()
    return users


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> User:
    """
    Get user by ID (admin only).

    Args:
        user_id: User ID
        current_user: Admin user
        db: Database session

    Returns:
        User data

    Raises:
        HTTPException: If user not found
    """
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: UUID,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> None:
    """
    Delete user (admin only).

    Args:
        user_id: User ID to delete
        current_user: Admin user
        db: Database session

    Raises:
        HTTPException: If user not found
    """
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    db.delete(user)
    db.commit()
