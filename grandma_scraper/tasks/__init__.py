"""Background tasks for asynchronous job execution."""

from grandma_scraper.tasks.celery_app import celery_app
from grandma_scraper.tasks.scrape import run_scrape_task

__all__ = ["celery_app", "run_scrape_task"]
