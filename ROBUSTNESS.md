# 🛡️ GrandmaScraper Robustness Features

This document describes all the robustness, reliability, and production-readiness features built into GrandmaScraper.

---

## Table of Contents

- [Error Handling & Retry Logic](#error-handling--retry-logic)
- [Rate Limiting](#rate-limiting)
- [Health Checks & Monitoring](#health-checks--monitoring)
- [Structured Logging](#structured-logging)
- [Circuit Breaker Pattern](#circuit-breaker-pattern)
- [Timeout Handling](#timeout-handling)
- [Security Features](#security-features)
- [Performance Optimization](#performance-optimization)

---

## Error Handling & Retry Logic

### Exponential Backoff Retry

All HTTP requests and browser operations automatically retry on failure with exponential backoff.

**Location:** `grandma_scraper/utils/retry.py`

**Features:**
- Configurable retry attempts (default: 3)
- Exponential delay between retries (1s → 2s → 4s)
- Maximum delay cap to prevent infinite waits
- Selective exception handling
- Detailed logging of retry attempts

**Usage Example:**
```python
from grandma_scraper.utils.retry import exponential_backoff

@exponential_backoff(
    max_retries=5,
    base_delay=2.0,
    max_delay=60.0,
    exceptions=(httpx.HTTPError, httpx.TimeoutException)
)
async def fetch_data(url):
    # Your code here
    pass
```

**Applied To:**
- `RequestsFetcher.fetch()` - HTTP requests with 3 retries, 2s base delay
- `BrowserFetcher.fetch()` - Browser automation with 2 retries, 3s base delay
- All database operations
- Redis connections

**Benefits:**
- Automatic recovery from transient failures
- Network hiccups don't crash scraping jobs
- Graceful degradation under load

---

## Circuit Breaker Pattern

Prevents cascading failures by failing fast when a service is down.

**Location:** `grandma_scraper/utils/retry.py`

**How It Works:**
1. **CLOSED**: Normal operation, requests pass through
2. **OPEN**: After 5 consecutive failures, fail immediately
3. **HALF_OPEN**: After 60s timeout, test if service recovered

**Usage Example:**
```python
from grandma_scraper.utils.retry import CircuitBreaker

breaker = CircuitBreaker(
    failure_threshold=5,
    recovery_timeout=60.0
)

async def fetch_with_circuit_breaker(url):
    return await breaker.async_call(fetch_function, url)
```

**Benefits:**
- Prevents resource exhaustion
- Faster failure detection
- Automatic service recovery testing
- Protects downstream services

---

## Rate Limiting

### API Rate Limiting

Token bucket algorithm to prevent API abuse and ensure fair usage.

**Location:** `grandma_scraper/api/middleware/rate_limit.py`

**Configuration:**
- **60 requests per minute** per IP address
- **10 request burst** capacity
- Automatic rate limit headers in responses

**Headers:**
```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
Retry-After: 5
```

**Features:**
- Per-IP tracking
- X-Forwarded-For support (proxy-aware)
- Graceful 429 responses
- Configurable limits per endpoint

**Bypass:**
Health check endpoints (`/api/v1/health`, `/api/v1/readiness`, `/api/v1/liveness`) are excluded from rate limiting.

### Scraping Rate Limiting

Built into the core scraping engine to respect websites.

**Configuration:**
- `rate_limit`: Delay between requests (seconds)
- `min_delay_ms` / `max_delay_ms`: Random delay range
- `respect_robots_txt`: Honor robots.txt directives

**Example:**
```yaml
config:
  rate_limit: 2.0  # 2 seconds between requests
  min_delay_ms: 1000
  max_delay_ms: 3000
  respect_robots_txt: true
```

---

## Health Checks & Monitoring

### Comprehensive Health Endpoint

**Endpoint:** `GET /api/v1/health`

**Checks:**
- ✅ PostgreSQL database connectivity
- ✅ Redis connectivity (Celery broker)
- ✅ Celery worker availability
- ✅ System resource usage (CPU, memory, disk)

**Response Example:**
```json
{
  "status": "healthy",
  "version": "0.4.0",
  "timestamp": "2024-01-15T10:30:00Z",
  "components": {
    "database": {
      "status": "ok",
      "message": "PostgreSQL connection successful",
      "response_time_ms": 5.23
    },
    "redis": {
      "status": "ok",
      "message": "Redis connection successful",
      "response_time_ms": 2.14
    },
    "celery": {
      "status": "ok",
      "message": "3 worker(s) active"
    }
  },
  "system_metrics": {
    "cpu_percent": 24.5,
    "memory_percent": 45.2,
    "disk_percent": 68.1
  }
}
```

**Status Levels:**
- `healthy` - All systems operational
- `degraded` - Some non-critical issues (e.g., high CPU)
- `unhealthy` - Critical component failure

### Kubernetes-Ready Probes

**Readiness Probe:** `GET /api/v1/readiness`
- Returns `ready: true` only when all critical services are available
- Use for load balancer health checks

**Liveness Probe:** `GET /api/v1/liveness`
- Simple check that application is running
- Use to detect deadlocks/hangs

**Kubernetes Configuration:**
```yaml
livenessProbe:
  httpGet:
    path: /api/v1/liveness
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 5

readinessProbe:
  httpGet:
    path: /api/v1/readiness
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 10
```

---

## Structured Logging

### JSON Logging

Production-grade structured logging for easy parsing and analysis.

**Location:** `grandma_scraper/utils/logging_config.py`

**Features:**
- JSON format for machine-readable logs
- ISO 8601 timestamps
- Contextual metadata (request ID, user, duration)
- Log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Automatic request/response logging

**Log Example:**
```json
{
  "timestamp": "2024-01-15T10:30:15.123Z",
  "level": "INFO",
  "logger": "grandma_scraper.api.main",
  "message": "GET /api/v1/jobs",
  "method": "GET",
  "path": "/api/v1/jobs",
  "status_code": 200,
  "duration_ms": 45.23,
  "client": "192.168.1.100"
}
```

### Request Logging Middleware

Every API request is automatically logged with:
- HTTP method and path
- Status code
- Response time (milliseconds)
- Client IP address
- Error details (if applicable)

**Integration with ELK Stack:**
```bash
# Ship logs to Elasticsearch
uvicorn grandma_scraper.api.main:app --log-config logging_config.json
```

**Setup:**
```python
from grandma_scraper.utils.logging_config import setup_logging

# Configure logging
setup_logging(
    level="INFO",
    json_format=True,
    log_file="/var/log/grandmascraper/app.log"
)

# Use structured logger
from grandma_scraper.utils.logging_config import get_logger

logger = get_logger(__name__)
logger.info("Scraping started", job_id=job.id, url=url)
```

---

## Timeout Handling

### HTTP Request Timeouts

All HTTP requests have configurable timeouts to prevent hanging.

**RequestsFetcher:**
- Default: 30 seconds
- Configurable per job

**BrowserFetcher:**
- Navigation timeout: 30 seconds (configurable)
- Wait states: networkidle, domcontentloaded, load
- Automatic page close on timeout

**Configuration:**
```python
fetcher = RequestsFetcher(timeout=60)  # 60 second timeout
fetcher = BrowserFetcher(timeout=45, wait_until="networkidle")
```

### Database Query Timeouts

- Connection pool timeout: 30s
- Query execution timeout: 60s (via statement_timeout)

### Celery Task Timeouts

Background tasks have time limits to prevent runaway processes.

**Configuration:**
```python
# In celery config
task_time_limit = 3600  # Hard limit: 1 hour
task_soft_time_limit = 3300  # Soft limit: 55 minutes
```

---

## Security Features

### Input Validation

All API inputs are validated using Pydantic models.

**Features:**
- Type checking
- Range validation
- Pattern matching (URLs, emails)
- Required field enforcement
- SQL injection prevention (via ORM)

**Example:**
```python
class ScrapeJobCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    config: ScrapeJobConfig

    @validator('config')
    def validate_config(cls, v):
        if not v.start_url.startswith(('http://', 'https://')):
            raise ValueError('Invalid URL')
        return v
```

### Authentication & Authorization

- JWT token-based authentication
- Password hashing with bcrypt
- Token expiration (30 minutes default)
- Role-based access control (admin, user, readonly)

### CORS Configuration

- Configurable allowed origins
- Credentials support
- Preflight request handling

**Production Setup:**
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Specific domain
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)
```

### robots.txt Compliance

Built-in robots.txt checking to respect website policies.

**Features:**
- Automatic robots.txt fetching
- User-agent directive support
- Crawl-delay compliance
- Disallow pattern matching

---

## Performance Optimization

### Connection Pooling

**HTTP Connections:**
- Persistent connections via httpx
- Connection reuse across requests
- Automatic keep-alive

**Database:**
- SQLAlchemy connection pooling
- Pool size: 20 connections
- Max overflow: 40 connections
- Connection pre-ping for stale detection

**Redis:**
- Connection pool for Celery
- Automatic reconnection

### Async/Await

- Non-blocking I/O throughout
- Concurrent request handling
- Efficient resource utilization

### Caching

**Browser Instances:**
- Reuse browser contexts
- Lazy initialization
- Automatic cleanup

**Static Content:**
- BeautifulSoup parsing caching
- Selector compilation caching

---

## Error Recovery Strategies

### Database Failures

1. **Connection lost** → Automatic reconnection with exponential backoff
2. **Query timeout** → Retry with increased timeout
3. **Deadlock** → Automatic retry (SQLAlchemy handles this)
4. **Constraint violation** → Detailed error message, no retry

### Network Failures

1. **Timeout** → Retry with exponential backoff (3 attempts)
2. **Connection refused** → Retry after delay
3. **DNS failure** → Fail fast, log error
4. **SSL error** → Retry once, then fail

### Browser Automation Failures

1. **Page crash** → Retry in new context
2. **Navigation timeout** → Retry with increased timeout
3. **Element not found** → Log warning, continue (optional field)
4. **JavaScript error** → Log error, continue with partial data

---

## Monitoring Best Practices

### Metrics to Track

1. **Request metrics:**
   - Request count by endpoint
   - Response time percentiles (p50, p95, p99)
   - Error rate by status code

2. **Scraping metrics:**
   - Jobs completed/failed
   - Pages scraped per job
   - Items extracted per job
   - Scraping duration

3. **System metrics:**
   - CPU usage
   - Memory usage
   - Disk I/O
   - Network I/O

4. **Queue metrics:**
   - Celery queue length
   - Worker utilization
   - Task success/failure rate

### Alerting

Set up alerts for:
- 🚨 Health check failures
- 🚨 Error rate > 5%
- 🚨 Response time p95 > 5s
- 🚨 Memory usage > 90%
- 🚨 No active Celery workers
- 🚨 Database connection errors

---

## Production Checklist

Before deploying to production:

- [ ] Configure CORS for your domain only
- [ ] Set strong `SECRET_KEY` (>= 32 characters)
- [ ] Use PostgreSQL (not SQLite)
- [ ] Set up database backups
- [ ] Configure log aggregation (ELK, CloudWatch, etc.)
- [ ] Set up monitoring (Prometheus, Datadog, etc.)
- [ ] Configure alerts for critical failures
- [ ] Enable HTTPS (use nginx/Caddy reverse proxy)
- [ ] Set rate limits appropriate for your traffic
- [ ] Configure Celery worker autoscaling
- [ ] Set up health check endpoints in load balancer
- [ ] Test disaster recovery procedures
- [ ] Document runbook for common issues

---

## Troubleshooting

### High Error Rate

1. Check health endpoint: `/api/v1/health`
2. Review logs for patterns
3. Verify database/Redis connectivity
4. Check system resources
5. Increase timeout values if needed
6. Scale Celery workers if queue is backing up

### Slow Responses

1. Check system metrics (CPU, memory)
2. Review slow query logs
3. Increase database connection pool size
4. Add caching layer (Redis)
5. Profile code with cProfile
6. Consider horizontal scaling

### Memory Leaks

1. Check for unclosed connections
2. Monitor Celery worker memory
3. Restart workers periodically
4. Verify browser instances are closed
5. Use memory profiling tools

---

## Summary

GrandmaScraper includes enterprise-grade robustness features:

- ✅ **Automatic retry logic** with exponential backoff
- ✅ **Circuit breaker** pattern for fault isolation
- ✅ **Rate limiting** to prevent abuse
- ✅ **Comprehensive health checks** (database, Redis, Celery, system)
- ✅ **Structured logging** for production monitoring
- ✅ **Timeout handling** at all layers
- ✅ **Input validation** and security hardening
- ✅ **Connection pooling** for performance
- ✅ **Kubernetes-ready** health probes
- ✅ **Error recovery** strategies for all failure modes

These features ensure GrandmaScraper is production-ready and can handle real-world challenges at scale.
