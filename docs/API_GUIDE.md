# API Guide

GrandmaScraper API provides a RESTful interface for managing scraping jobs, user authentication, and result retrieval.

## Quick Start

### 1. Start the API Server

**Using Docker Compose (Recommended):**

```bash
docker-compose up -d
```

**Manually:**

```bash
# Start PostgreSQL and Redis first, then:
uvicorn grandma_scraper.api.main:app --reload
```

### 2. Access API Documentation

- **Interactive API Docs (Swagger UI)**: http://localhost:8000/api/docs
- **Alternative Docs (ReDoc)**: http://localhost:8000/api/redoc
- **OpenAPI Schema**: http://localhost:8000/api/openapi.json

## Authentication

All API endpoints (except registration and login) require authentication using JWT tokens.

### Register a New User

```bash
POST /api/v1/auth/register

{
  "email": "user@example.com",
  "username": "myusername",
  "password": "securepassword123"
}
```

### Login

```bash
POST /api/v1/auth/token

# Form data:
username=user@example.com
password=securepassword123
```

**Response:**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

### Use Token in Requests

Include the token in the `Authorization` header:

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

## API Endpoints

### Health Check

```bash
GET /api/v1/health
```

Returns system health status.

### Users

#### Get Current User

```bash
GET /api/v1/users/me
Authorization: Bearer <token>
```

#### Update Current User

```bash
PUT /api/v1/users/me
Authorization: Bearer <token>

{
  "username": "newname",
  "email": "newemail@example.com"
}
```

### Jobs

#### Create a Job

```bash
POST /api/v1/jobs/
Authorization: Bearer <token>

{
  "name": "My Scraper",
  "description": "Scrapes product data",
  "enabled": true,
  "config": {
    "name": "Product Scraper",
    "start_url": "https://example.com/products",
    "item_selector": ".product",
    "fields": [
      {
        "name": "title",
        "selector": ".product-title",
        "attribute": "text"
      },
      {
        "name": "price",
        "selector": ".price",
        "attribute": "text"
      }
    ],
    "pagination": {
      "type": "next_button",
      "next_button_selector": ".next"
    },
    "max_pages": 10
  }
}
```

#### List Jobs

```bash
GET /api/v1/jobs/?skip=0&limit=100
Authorization: Bearer <token>
```

#### Get Job by ID

```bash
GET /api/v1/jobs/{job_id}
Authorization: Bearer <token>
```

#### Update Job

```bash
PUT /api/v1/jobs/{job_id}
Authorization: Bearer <token>

{
  "name": "Updated Name",
  "enabled": false
}
```

#### Delete Job

```bash
DELETE /api/v1/jobs/{job_id}
Authorization: Bearer <token>
```

#### Run a Job

```bash
POST /api/v1/jobs/{job_id}/run
Authorization: Bearer <token>
```

**Response:**

```json
{
  "message": "Scraping job started",
  "job_id": "uuid",
  "result_id": "uuid"
}
```

### Results

#### List Results

```bash
GET /api/v1/results/?skip=0&limit=100
Authorization: Bearer <token>

# Filter by job:
GET /api/v1/results/?job_id={job_id}
```

#### Get Result by ID

```bash
GET /api/v1/results/{result_id}
Authorization: Bearer <token>
```

#### Export Result as CSV

```bash
GET /api/v1/results/{result_id}/export/csv
Authorization: Bearer <token>
```

Downloads CSV file.

#### Delete Result

```bash
DELETE /api/v1/results/{result_id}
Authorization: Bearer <token>
```

## Example Workflows

### Workflow 1: Create and Run a Job

```bash
# 1. Register
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","username":"user","password":"pass123"}'

# 2. Login
TOKEN=$(curl -X POST http://localhost:8000/api/v1/auth/token \
  -d "username=user@example.com&password=pass123" | jq -r '.access_token')

# 3. Create Job
JOB_ID=$(curl -X POST http://localhost:8000/api/v1/jobs/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d @job_config.json | jq -r '.id')

# 4. Run Job
RESULT=$(curl -X POST http://localhost:8000/api/v1/jobs/$JOB_ID/run \
  -H "Authorization: Bearer $TOKEN")

# 5. Get Result
RESULT_ID=$(echo $RESULT | jq -r '.result_id')
curl -X GET http://localhost:8000/api/v1/results/$RESULT_ID \
  -H "Authorization: Bearer $TOKEN"

# 6. Export CSV
curl -X GET http://localhost:8000/api/v1/results/$RESULT_ID/export/csv \
  -H "Authorization: Bearer $TOKEN" \
  -o results.csv
```

## Error Handling

The API returns standard HTTP status codes:

- **200 OK**: Success
- **201 Created**: Resource created
- **204 No Content**: Success with no response body
- **400 Bad Request**: Invalid request data
- **401 Unauthorized**: Missing or invalid authentication
- **403 Forbidden**: Insufficient permissions
- **404 Not Found**: Resource not found
- **500 Internal Server Error**: Server error

**Error Response Format:**

```json
{
  "detail": "Error message"
}
```

## Rate Limiting

Currently no rate limiting is enforced. This will be added in a future version.

## Development

### Running Tests

```bash
# API tests
pytest tests/api/

# All tests
pytest
```

### Database Migrations

GrandmaScraper uses Alembic for database migrations.

```bash
# Create a migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Celery Worker

To process background jobs:

```bash
celery -A grandma_scraper.tasks.celery_app worker --loglevel=info
```

## Production Deployment

### Environment Variables

Create a `.env` file (see `.env.example`):

```env
# Database
POSTGRES_USER=grandma_scraper
POSTGRES_PASSWORD=strong_password_here
POSTGRES_SERVER=postgres
POSTGRES_PORT=5432
POSTGRES_DB=grandma_scraper

# Celery
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# Auth
SECRET_KEY=generate-a-long-random-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### Docker Deployment

```bash
# Build and start services
docker-compose up -d

# View logs
docker-compose logs -f api

# Stop services
docker-compose down
```

### Security Checklist

- [ ] Change `SECRET_KEY` to a strong random value
- [ ] Use strong database passwords
- [ ] Enable HTTPS in production
- [ ] Configure CORS origins properly
- [ ] Set up firewall rules
- [ ] Enable database backups
- [ ] Monitor logs for suspicious activity

## Monitoring

### Health Check

```bash
curl http://localhost:8000/api/v1/health
```

### Database Connection

The health endpoint reports database status.

## Support

- **Documentation**: [docs/](../docs/)
- **Issues**: [GitHub Issues](https://github.com/yourusername/grandma-scraper/issues)
- **API Docs**: http://localhost:8000/api/docs
