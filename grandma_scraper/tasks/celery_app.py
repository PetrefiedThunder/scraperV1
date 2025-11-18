"""
Celery application configuration.

Configures Celery for background task execution.
"""

import os
from celery import Celery


# Create Celery app
celery_app = Celery(
    "grandma_scraper",
    broker=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0"),
    include=["grandma_scraper.tasks.scrape"],
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max per task
    task_soft_time_limit=3300,  # 55 minutes soft limit
)

if __name__ == "__main__":
    celery_app.start()
