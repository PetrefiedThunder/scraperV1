"""
Background scraping tasks.

Celery tasks for executing scrape jobs asynchronously.
"""

import asyncio
from uuid import UUID
from typing import Optional

from grandma_scraper.tasks.celery_app import celery_app
from grandma_scraper.db.session import SessionLocal
from grandma_scraper.db.models import ScrapeJobDB, ScrapeResultDB, JobStatus
from grandma_scraper.core.models import ScrapeJob
from grandma_scraper.core.engine import ScrapeEngine
from grandma_scraper.utils.logger import get_logger


logger = get_logger(__name__)


def run_scrape_task(job_id: str, result_id: str) -> None:
    """
    Run scraping task synchronously (for FastAPI BackgroundTasks).

    This is a simplified version that runs directly without Celery.
    For full Celery support, use run_scrape_task_celery.

    Args:
        job_id: Job ID string
        result_id: Result ID string
    """
    asyncio.run(_run_scrape_async(job_id, result_id))


async def _run_scrape_async(job_id: str, result_id: str) -> None:
    """
    Execute scraping job asynchronously.

    Args:
        job_id: Job ID string
        result_id: Result ID string
    """
    db = SessionLocal()
    job_uuid = UUID(job_id)
    result_uuid = UUID(result_id)

    try:
        # Get job and result from database
        job_db = db.query(ScrapeJobDB).filter(ScrapeJobDB.id == job_uuid).first()
        result_db = db.query(ScrapeResultDB).filter(ScrapeResultDB.id == result_uuid).first()

        if not job_db or not result_db:
            logger.error(f"Job or result not found: job_id={job_id}, result_id={result_id}")
            return

        # Create ScrapeJob from config
        scrape_job = ScrapeJob(**job_db.config)

        # Create engine and run
        logger.info(f"Starting scrape job: {job_db.name} (ID: {job_id})")

        engine = ScrapeEngine(scrape_job)
        result = await engine.run()

        # Update result in database
        result_db.status = JobStatus(result.status.value)
        result_db.items = result.items
        result_db.total_items = result.total_items
        result_db.pages_scraped = result.pages_scraped
        result_db.started_at = result.started_at
        result_db.completed_at = result.completed_at
        result_db.duration_seconds = result.duration_seconds
        result_db.error_message = result.error_message
        result_db.error_details = result.error_details
        result_db.warnings = result.warnings

        db.commit()

        logger.info(
            f"Scrape job completed: {job_db.name} - "
            f"Items: {result.total_items}, Pages: {result.pages_scraped}"
        )

    except Exception as e:
        logger.error(f"Scrape job failed: {str(e)}", exc_info=True)

        # Mark as failed
        result_db = db.query(ScrapeResultDB).filter(ScrapeResultDB.id == result_uuid).first()
        if result_db:
            result_db.status = JobStatus.FAILED
            result_db.error_message = str(e)
            db.commit()

    finally:
        db.close()


@celery_app.task(name="grandma_scraper.tasks.scrape.run_scrape_task_celery")
def run_scrape_task_celery(job_id: str, result_id: str) -> dict:
    """
    Celery task for running scrape jobs.

    This is the full Celery version for distributed task execution.

    Args:
        job_id: Job ID string
        result_id: Result ID string

    Returns:
        Task result summary
    """
    try:
        run_scrape_task(job_id, result_id)

        return {
            "status": "completed",
            "job_id": job_id,
            "result_id": result_id,
        }

    except Exception as e:
        logger.error(f"Celery task failed: {str(e)}", exc_info=True)

        return {
            "status": "failed",
            "job_id": job_id,
            "result_id": result_id,
            "error": str(e),
        }
