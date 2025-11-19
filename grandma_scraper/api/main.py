"""
Main FastAPI application.

Creates and configures the FastAPI app with all routes and middleware.
"""

import logging
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
from starlette.exceptions import HTTPException as StarletteHTTPException

from grandma_scraper import __version__
from grandma_scraper.api.routers import auth, jobs, results, users, health, websocket
from grandma_scraper.api.middleware.rate_limit import RateLimitMiddleware
from grandma_scraper.api.middleware.request_id import RequestIDMiddleware
from grandma_scraper.api.middleware.metrics import PrometheusMiddleware, metrics_endpoint
from grandma_scraper.api.middleware.compression import GZipMiddleware
from grandma_scraper.utils.logging_config import setup_logging
from grandma_scraper.db import Base, engine

# Setup structured logging
setup_logging(level="INFO", json_format=False)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Handles startup and shutdown events.
    """
    logger.info("Starting GrandmaScraper API", extra={"version": __version__})

    # Startup: Create database tables
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created/verified")

    yield

    # Shutdown: Clean up resources
    logger.info("Shutting down GrandmaScraper API")


def create_app() -> FastAPI:
    """
    Create and configure FastAPI application.

    Returns:
        Configured FastAPI application instance
    """
    app = FastAPI(
        title="GrandmaScraper API",
        description="""
## Production-Grade Web Scraping API

GrandmaScraper provides a powerful yet user-friendly web scraping platform with:

### Features
* 🎯 **Visual Selector Picker** - Click-to-select CSS selectors (no coding needed!)
* 📅 **Job Scheduling** - Schedule scraping jobs with cron expressions
* 🔄 **Real-time Updates** - WebSocket support for live progress tracking
* 📊 **Export Formats** - JSON, CSV, Excel support
* 🔐 **Authentication** - JWT-based secure access
* 📈 **Monitoring** - Prometheus metrics and health checks
* 🪝 **Webhooks** - Get notified when jobs complete
* ⚡ **Production Ready** - Rate limiting, GZIP compression, structured logging

### API Capabilities
* Create and manage scraping jobs with custom configurations
* Execute jobs immediately or schedule for later
* Monitor job progress in real-time via WebSocket
* Download results in multiple formats
* Manage user accounts and authentication

### Performance & Reliability
* Automatic retry with exponential backoff
* Circuit breaker for fault tolerance
* Request ID tracking for distributed tracing
* Comprehensive health monitoring
* Database query optimization with indexes
        """,
        version=__version__,
        lifespan=lifespan,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
        contact={
            "name": "GrandmaScraper Team",
            "url": "https://github.com/yourusername/grandma-scraper",
        },
        license_info={
            "name": "MIT License",
            "url": "https://opensource.org/licenses/MIT",
        },
        openapi_tags=[
            {
                "name": "Authentication",
                "description": "User authentication and registration endpoints. Use `/auth/login` to obtain JWT tokens.",
            },
            {
                "name": "Jobs",
                "description": "Manage scraping jobs. Create, update, delete, and execute scraping configurations.",
            },
            {
                "name": "Results",
                "description": "Access scraping results. View, download, and export scraped data in various formats.",
            },
            {
                "name": "Users",
                "description": "User management endpoints. View and update user profiles.",
            },
            {
                "name": "Health",
                "description": "Health check endpoints for monitoring. Includes Kubernetes-ready liveness/readiness probes.",
            },
            {
                "name": "WebSocket",
                "description": "Real-time WebSocket connections for job progress updates.",
            },
            {
                "name": "Monitoring",
                "description": "Prometheus metrics endpoint for monitoring and observability.",
            },
        ],
    )

    # Add middleware in order (last added = first executed)
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure based on environment in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Rate limiting middleware (60 requests per minute)
    app.add_middleware(
        RateLimitMiddleware,
        requests_per_minute=60,
        burst_size=10,
    )

    # GZIP compression middleware
    app.add_middleware(
        GZipMiddleware,
        minimum_size=500,
        compression_level=6,
    )

    # Prometheus metrics middleware
    app.add_middleware(
        PrometheusMiddleware,
        exclude_paths=['/metrics', '/health', '/readiness', '/liveness'],
    )

    # Request ID middleware (should be early to ensure all requests get IDs)
    app.add_middleware(RequestIDMiddleware)

    # Global exception handlers
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        """Handle HTTP exceptions with structured logging"""
        logger.warning(
            f"HTTP {exc.status_code}: {exc.detail}",
            extra={
                "path": request.url.path,
                "method": request.method,
                "status_code": exc.status_code,
                "client": request.client.host if request.client else "unknown",
            }
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Handle validation errors with detailed logging"""
        logger.warning(
            "Validation error",
            extra={
                "path": request.url.path,
                "method": request.method,
                "errors": exc.errors(),
            }
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": exc.errors(), "body": exc.body},
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Catch-all handler for unexpected exceptions"""
        logger.error(
            f"Unhandled exception: {str(exc)}",
            exc_info=True,
            extra={
                "path": request.url.path,
                "method": request.method,
                "exception_type": type(exc).__name__,
            }
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error"},
        )

    # Request logging middleware
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        """Log all HTTP requests"""
        import time
        start_time = time.time()

        response = await call_next(request)

        duration = time.time() - start_time
        logger.info(
            f"{request.method} {request.url.path}",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": round(duration * 1000, 2),
                "client": request.client.host if request.client else "unknown",
            }
        )

        return response

    # Include routers
    app.include_router(health.router, prefix="/api/v1", tags=["Health"])
    app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
    app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])
    app.include_router(jobs.router, prefix="/api/v1/jobs", tags=["Jobs"])
    app.include_router(results.router, prefix="/api/v1/results", tags=["Results"])
    app.include_router(websocket.router, prefix="/api/v1", tags=["WebSocket"])

    # Add metrics endpoint
    app.add_api_route("/metrics", metrics_endpoint, methods=["GET"], tags=["Monitoring"])

    logger.info("FastAPI application configured successfully")

    return app


# Create app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
