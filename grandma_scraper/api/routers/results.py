"""
Results endpoints.

Handles scraping result queries and exports.
"""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session

from grandma_scraper.auth import get_current_active_user
from grandma_scraper.api.schemas import ResultResponse
from grandma_scraper.db import get_db
from grandma_scraper.db.models import User, ScrapeResultDB, ScrapeJobDB
from grandma_scraper.core.exporters import DataExporter
import io
import csv


router = APIRouter()


@router.get("/", response_model=List[ResultResponse])
async def list_results(
    job_id: UUID = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> List[ScrapeResultDB]:
    """
    List scraping results.

    Args:
        job_id: Optional filter by job ID
        skip: Number of records to skip
        limit: Maximum number of records to return
        current_user: Authenticated user
        db: Database session

    Returns:
        List of results for user's jobs
    """
    query = (
        db.query(ScrapeResultDB)
        .join(ScrapeJobDB)
        .filter(ScrapeJobDB.owner_id == current_user.id)
    )

    if job_id:
        query = query.filter(ScrapeResultDB.job_id == job_id)

    results = query.order_by(ScrapeResultDB.created_at.desc()).offset(skip).limit(limit).all()

    return results


@router.get("/{result_id}", response_model=ResultResponse)
async def get_result(
    result_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> ScrapeResultDB:
    """
    Get result by ID.

    Args:
        result_id: Result ID
        current_user: Authenticated user
        db: Database session

    Returns:
        Result data

    Raises:
        HTTPException: If result not found or access denied
    """
    result = (
        db.query(ScrapeResultDB)
        .join(ScrapeJobDB)
        .filter(ScrapeResultDB.id == result_id)
        .filter(ScrapeJobDB.owner_id == current_user.id)
        .first()
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Result not found",
        )

    return result


@router.get("/{result_id}/export/csv")
async def export_result_csv(
    result_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Response:
    """
    Export result as CSV.

    Args:
        result_id: Result ID
        current_user: Authenticated user
        db: Database session

    Returns:
        CSV file download

    Raises:
        HTTPException: If result not found or access denied
    """
    result = (
        db.query(ScrapeResultDB)
        .join(ScrapeJobDB)
        .filter(ScrapeResultDB.id == result_id)
        .filter(ScrapeJobDB.owner_id == current_user.id)
        .first()
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Result not found",
        )

    if not result.items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No data to export",
        )

    # Create CSV in memory
    output = io.StringIO()

    # Get all unique keys
    fieldnames = set()
    for item in result.items:
        fieldnames.update(item.keys())
    fieldnames = sorted(fieldnames)

    # Write CSV
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(result.items)

    csv_content = output.getvalue()

    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=result_{result_id}.csv"
        },
    )


@router.delete("/{result_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_result(
    result_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> None:
    """
    Delete result.

    Args:
        result_id: Result ID to delete
        current_user: Authenticated user
        db: Database session

    Raises:
        HTTPException: If result not found or access denied
    """
    result = (
        db.query(ScrapeResultDB)
        .join(ScrapeJobDB)
        .filter(ScrapeResultDB.id == result_id)
        .filter(ScrapeJobDB.owner_id == current_user.id)
        .first()
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Result not found",
        )

    db.delete(result)
    db.commit()
