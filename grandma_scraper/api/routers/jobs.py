"""
Job management endpoints.

Handles scraping job CRUD and execution.
"""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session

from grandma_scraper.auth import get_current_active_user
from grandma_scraper.api.schemas import JobCreate, JobUpdate, JobResponse
from grandma_scraper.db import get_db
from grandma_scraper.db.models import User, ScrapeJobDB, ScrapeResultDB, JobStatus
from grandma_scraper.core.models import ScrapeJob
from grandma_scraper.tasks.scrape import run_scrape_task


router = APIRouter()


@router.post("/", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(
    job_data: JobCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> ScrapeJobDB:
    """
    Create a new scraping job.

    Args:
        job_data: Job creation data
        current_user: Authenticated user
        db: Database session

    Returns:
        Created job

    Raises:
        HTTPException: If config is invalid
    """
    # Validate config by trying to create a ScrapeJob
    try:
        ScrapeJob(**job_data.config)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid job configuration: {str(e)}",
        )

    # Create job
    new_job = ScrapeJobDB(
        name=job_data.name,
        description=job_data.description,
        config=job_data.config,
        enabled=job_data.enabled,
        owner_id=current_user.id,
    )

    db.add(new_job)
    db.commit()
    db.refresh(new_job)

    return new_job


@router.get("/", response_model=List[JobResponse])
async def list_jobs(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> List[ScrapeJobDB]:
    """
    List user's scraping jobs.

    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        current_user: Authenticated user
        db: Database session

    Returns:
        List of jobs owned by user
    """
    jobs = (
        db.query(ScrapeJobDB)
        .filter(ScrapeJobDB.owner_id == current_user.id)
        .offset(skip)
        .limit(limit)
        .all()
    )

    return jobs


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> ScrapeJobDB:
    """
    Get job by ID.

    Args:
        job_id: Job ID
        current_user: Authenticated user
        db: Database session

    Returns:
        Job data

    Raises:
        HTTPException: If job not found or access denied
    """
    job = db.query(ScrapeJobDB).filter(ScrapeJobDB.id == job_id).first()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    # Check ownership
    if job.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this job",
        )

    return job


@router.put("/{job_id}", response_model=JobResponse)
async def update_job(
    job_id: UUID,
    job_update: JobUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> ScrapeJobDB:
    """
    Update job.

    Args:
        job_id: Job ID
        job_update: Job update data
        current_user: Authenticated user
        db: Database session

    Returns:
        Updated job

    Raises:
        HTTPException: If job not found, access denied, or invalid config
    """
    job = db.query(ScrapeJobDB).filter(ScrapeJobDB.id == job_id).first()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    # Check ownership
    if job.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this job",
        )

    # Validate new config if provided
    if job_update.config:
        try:
            ScrapeJob(**job_update.config)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid job configuration: {str(e)}",
            )

    # Update fields
    if job_update.name:
        job.name = job_update.name
    if job_update.description is not None:
        job.description = job_update.description
    if job_update.config:
        job.config = job_update.config
    if job_update.enabled is not None:
        job.enabled = job_update.enabled

    db.commit()
    db.refresh(job)

    return job


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job(
    job_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> None:
    """
    Delete job.

    Args:
        job_id: Job ID to delete
        current_user: Authenticated user
        db: Database session

    Raises:
        HTTPException: If job not found or access denied
    """
    job = db.query(ScrapeJobDB).filter(ScrapeJobDB.id == job_id).first()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    # Check ownership
    if job.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this job",
        )

    db.delete(job)
    db.commit()


@router.post("/{job_id}/run", status_code=status.HTTP_202_ACCEPTED)
async def run_job(
    job_id: UUID,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> dict:
    """
    Run a scraping job.

    Starts job execution in the background.

    Args:
        job_id: Job ID to run
        background_tasks: FastAPI background tasks
        current_user: Authenticated user
        db: Database session

    Returns:
        Execution status with result ID

    Raises:
        HTTPException: If job not found, access denied, or disabled
    """
    job = db.query(ScrapeJobDB).filter(ScrapeJobDB.id == job_id).first()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    # Check ownership
    if job.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to run this job",
        )

    # Check if job is enabled
    if not job.enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job is disabled",
        )

    # Create result record
    result = ScrapeResultDB(
        job_id=job.id,
        status=JobStatus.PENDING,
    )

    db.add(result)
    db.commit()
    db.refresh(result)

    # Start scraping in background
    background_tasks.add_task(run_scrape_task, str(job.id), str(result.id))

    return {
        "message": "Scraping job started",
        "job_id": str(job.id),
        "result_id": str(result.id),
    }
