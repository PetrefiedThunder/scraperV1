"""
Health check endpoints.

Provides system health and status information.
"""

import psutil
import redis
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Dict, Optional
import logging
from datetime import datetime

from grandma_scraper import __version__
from grandma_scraper.db import get_db

logger = logging.getLogger(__name__)

router = APIRouter()


class ComponentHealth(BaseModel):
    """Health status for a component."""
    status: str  # "ok", "degraded", "error"
    message: Optional[str] = None
    response_time_ms: Optional[float] = None


class SystemMetrics(BaseModel):
    """System resource metrics."""
    cpu_percent: float
    memory_percent: float
    disk_percent: float


class HealthResponse(BaseModel):
    """Comprehensive health check response."""
    status: str  # "healthy", "degraded", "unhealthy"
    version: str
    timestamp: str
    components: Dict[str, ComponentHealth]
    system_metrics: Optional[SystemMetrics] = None


class ReadinessResponse(BaseModel):
    """Readiness check response (for Kubernetes)."""
    ready: bool
    message: Optional[str] = None


@router.get("/health", response_model=HealthResponse)
async def health_check(db: Session = Depends(get_db)) -> HealthResponse:
    """
    Comprehensive health check endpoint.

    Checks:
    - Database connectivity
    - Redis connectivity
    - Celery worker status
    - System resource usage

    Returns:
        Detailed health status response
    """
    components = {}
    overall_status = "healthy"

    # Check database
    import time
    start = time.time()
    try:
        db.execute("SELECT 1")
        db_time = (time.time() - start) * 1000
        components["database"] = ComponentHealth(
            status="ok",
            message="PostgreSQL connection successful",
            response_time_ms=round(db_time, 2)
        )
    except Exception as e:
        components["database"] = ComponentHealth(
            status="error",
            message=f"Database connection failed: {str(e)}"
        )
        overall_status = "unhealthy"
        logger.error(f"Database health check failed: {e}")

    # Check Redis
    start = time.time()
    try:
        from grandma_scraper.core.config import settings
        redis_client = redis.from_url(settings.celery_broker_url)
        redis_client.ping()
        redis_time = (time.time() - start) * 1000
        components["redis"] = ComponentHealth(
            status="ok",
            message="Redis connection successful",
            response_time_ms=round(redis_time, 2)
        )
    except Exception as e:
        components["redis"] = ComponentHealth(
            status="error",
            message=f"Redis connection failed: {str(e)}"
        )
        if overall_status == "healthy":
            overall_status = "degraded"
        logger.error(f"Redis health check failed: {e}")

    # Check Celery workers
    try:
        from grandma_scraper.tasks.celery_app import celery_app
        inspect = celery_app.control.inspect(timeout=2.0)
        active_workers = inspect.active()

        if active_workers:
            worker_count = len(active_workers)
            components["celery"] = ComponentHealth(
                status="ok",
                message=f"{worker_count} worker(s) active"
            )
        else:
            components["celery"] = ComponentHealth(
                status="degraded",
                message="No active Celery workers found"
            )
            if overall_status == "healthy":
                overall_status = "degraded"
    except Exception as e:
        components["celery"] = ComponentHealth(
            status="error",
            message=f"Celery check failed: {str(e)}"
        )
        logger.error(f"Celery health check failed: {e}")

    # Collect system metrics
    try:
        system_metrics = SystemMetrics(
            cpu_percent=psutil.cpu_percent(interval=0.1),
            memory_percent=psutil.virtual_memory().percent,
            disk_percent=psutil.disk_usage('/').percent
        )

        # Warn if resources are high
        if system_metrics.cpu_percent > 90 or system_metrics.memory_percent > 90:
            if overall_status == "healthy":
                overall_status = "degraded"
    except Exception as e:
        logger.error(f"System metrics collection failed: {e}")
        system_metrics = None

    return HealthResponse(
        status=overall_status,
        version=__version__,
        timestamp=datetime.utcnow().isoformat(),
        components=components,
        system_metrics=system_metrics
    )


@router.get("/readiness", response_model=ReadinessResponse)
async def readiness_check(db: Session = Depends(get_db)) -> ReadinessResponse:
    """
    Readiness check for Kubernetes/load balancers.

    Returns ready=true only if all critical components are available.
    """
    try:
        # Check database
        db.execute("SELECT 1")

        # Check Redis
        from grandma_scraper.core.config import settings
        redis_client = redis.from_url(settings.celery_broker_url)
        redis_client.ping()

        return ReadinessResponse(ready=True)

    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return ReadinessResponse(
            ready=False,
            message=f"Service not ready: {str(e)}"
        )


@router.get("/liveness")
async def liveness_check():
    """
    Liveness check for Kubernetes.

    Simple check that the application is running.
    """
    return {"alive": True}
