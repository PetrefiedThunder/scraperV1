# Multi-stage Dockerfile for GrandmaScraper

FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements
COPY pyproject.toml ./

# Install Python dependencies
RUN pip install -e ".[dev]"

# Install Playwright browsers
RUN playwright install-deps && \
    playwright install chromium

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 scraper && \
    chown -R scraper:scraper /app

USER scraper

# Expose port
EXPOSE 8000

# Default command (can be overridden in docker-compose)
CMD ["uvicorn", "grandma_scraper.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
