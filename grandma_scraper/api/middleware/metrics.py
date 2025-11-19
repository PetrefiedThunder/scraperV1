"""
Prometheus metrics middleware for monitoring
"""

from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
import time

# Define Prometheus metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code']
)

REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

REQUEST_IN_PROGRESS = Gauge(
    'http_requests_in_progress',
    'HTTP requests currently being processed',
    ['method', 'endpoint']
)

SCRAPING_JOBS_TOTAL = Counter(
    'scraping_jobs_total',
    'Total scraping jobs executed',
    ['status']
)

SCRAPING_ITEMS_TOTAL = Counter(
    'scraping_items_total',
    'Total items scraped'
)

SCRAPING_PAGES_TOTAL = Counter(
    'scraping_pages_total',
    'Total pages scraped'
)

SCRAPING_DURATION = Histogram(
    'scraping_job_duration_seconds',
    'Scraping job duration in seconds'
)


class PrometheusMiddleware(BaseHTTPMiddleware):
    """
    Middleware to collect Prometheus metrics for all HTTP requests.

    Metrics collected:
    - Request count by method, endpoint, and status code
    - Request duration histogram
    - Requests in progress gauge
    """

    def __init__(self, app, exclude_paths: list = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or ['/metrics', '/health', '/readiness', '/liveness']

    async def dispatch(self, request: Request, call_next):
        # Skip metrics for excluded paths to avoid noise
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)

        method = request.method
        endpoint = request.url.path

        # Increment in-progress gauge
        REQUEST_IN_PROGRESS.labels(method=method, endpoint=endpoint).inc()

        start_time = time.time()

        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as e:
            status_code = 500
            raise
        finally:
            # Decrement in-progress gauge
            REQUEST_IN_PROGRESS.labels(method=method, endpoint=endpoint).dec()

            # Record duration
            duration = time.time() - start_time
            REQUEST_DURATION.labels(method=method, endpoint=endpoint).observe(duration)

            # Increment request counter
            REQUEST_COUNT.labels(
                method=method,
                endpoint=endpoint,
                status_code=status_code
            ).inc()

        return response


async def metrics_endpoint(request: Request):
    """
    Prometheus metrics endpoint.

    Returns metrics in Prometheus text format.
    """
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


def record_scraping_job(status: str, duration: float, items: int, pages: int):
    """
    Record metrics for a completed scraping job.

    Args:
        status: Job status (completed, failed, cancelled)
        duration: Job duration in seconds
        items: Number of items scraped
        pages: Number of pages scraped
    """
    SCRAPING_JOBS_TOTAL.labels(status=status).inc()
    SCRAPING_DURATION.observe(duration)
    SCRAPING_ITEMS_TOTAL.inc(items)
    SCRAPING_PAGES_TOTAL.inc(pages)
