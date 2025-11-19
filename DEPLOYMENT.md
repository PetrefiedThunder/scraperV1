# 🚀 GrandmaScraper Deployment Guide

This guide covers deploying GrandmaScraper in various environments.

## Table of Contents

- [Local Development](#local-development)
- [Docker Deployment](#docker-deployment)
- [Production Deployment](#production-deployment)
- [Environment Variables](#environment-variables)
- [Troubleshooting](#troubleshooting)

---

## Local Development

### Prerequisites

- Python 3.11+
- Node.js 18+ and npm
- PostgreSQL 14+ (or use Docker)
- Redis 7+ (or use Docker)

### Backend Setup

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/grandma-scraper.git
cd grandma-scraper

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -e ".[dev]"

# 4. Install Playwright browsers
playwright install chromium

# 5. Set up database (using Docker for convenience)
docker run -d \
  --name grandma-postgres \
  -e POSTGRES_USER=grandma_scraper \
  -e POSTGRES_PASSWORD=scraper_password \
  -e POSTGRES_DB=grandma_scraper \
  -p 5432:5432 \
  postgres:16-alpine

# 6. Set up Redis
docker run -d \
  --name grandma-redis \
  -p 6379:6379 \
  redis:7-alpine

# 7. Create .env file
cat > .env <<EOF
POSTGRES_USER=grandma_scraper
POSTGRES_PASSWORD=scraper_password
POSTGRES_SERVER=localhost
POSTGRES_PORT=5432
POSTGRES_DB=grandma_scraper
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
SECRET_KEY=$(openssl rand -hex 32)
EOF

# 8. Run database migrations
# (Tables are created automatically on first run)

# 9. Start the API server
uvicorn grandma_scraper.api.main:app --reload --port 8000

# 10. In a new terminal, start Celery worker
celery -A grandma_scraper.tasks.celery_app worker --loglevel=info
```

### Frontend Setup

```bash
# 1. Navigate to frontend directory
cd ui/grandma-scraper-ui

# 2. Install dependencies
npm install

# 3. Create .env file
cat > .env.local <<EOF
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_WS_BASE_URL=ws://localhost:8000/api/v1
EOF

# 4. Start development server
npm run dev
```

**Access the application:**
- Frontend: http://localhost:5173
- API Docs: http://localhost:8000/api/docs

---

## Docker Deployment

The easiest way to deploy GrandmaScraper is using Docker Compose.

### Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/grandma-scraper.git
cd grandma-scraper

# 2. Create production environment file
cat > .env.production <<EOF
POSTGRES_USER=grandma_scraper
POSTGRES_PASSWORD=$(openssl rand -base64 32)
SECRET_KEY=$(openssl rand -hex 32)
EOF

# 3. Start all services
docker-compose up -d

# 4. Check service status
docker-compose ps

# 5. View logs
docker-compose logs -f
```

**Access the application:**
- Frontend: http://localhost:3000
- API: http://localhost:8000
- API Docs: http://localhost:8000/api/docs

### Docker Services

The `docker-compose.yml` includes:

1. **postgres** - PostgreSQL database
2. **redis** - Redis for Celery task queue
3. **api** - FastAPI backend server
4. **celery_worker** - Background job processor
5. **frontend** - React UI (Vite dev server)

### Managing Docker Services

```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# Restart a specific service
docker-compose restart api

# View logs for a service
docker-compose logs -f api

# Execute commands in a container
docker-compose exec api bash

# Rebuild after code changes
docker-compose build
docker-compose up -d

# Remove all data (⚠️  destructive!)
docker-compose down -v
```

---

## Production Deployment

### Option 1: Docker Compose (Small-Medium Scale)

For production, update `docker-compose.yml`:

```yaml
services:
  api:
    restart: always
    environment:
      - SECRET_KEY=${SECRET_KEY}  # From env file
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G

  celery_worker:
    restart: always
    deploy:
      replicas: 3  # Scale workers
      resources:
        limits:
          cpus: '2'
          memory: 4G
```

### Option 2: Kubernetes (Large Scale)

Create Kubernetes manifests:

**Database (postgres-deployment.yaml):**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: postgres
spec:
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:16-alpine
        env:
        - name: POSTGRES_DB
          value: grandma_scraper
        - name: POSTGRES_USER
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: username
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: password
        ports:
        - containerPort: 5432
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
      volumes:
      - name: postgres-storage
        persistentVolumeClaim:
          claimName: postgres-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: postgres
spec:
  ports:
  - port: 5432
  selector:
    app: postgres
```

**API (api-deployment.yaml):**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: grandma-scraper-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: api
  template:
    metadata:
      labels:
        app: api
    spec:
      containers:
      - name: api
        image: your-registry/grandma-scraper:latest
        command: ["uvicorn", "grandma_scraper.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
        env:
        - name: POSTGRES_SERVER
          value: postgres
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: secret-key
        ports:
        - containerPort: 8000
---
apiVersion: v1
kind: Service
metadata:
  name: api
spec:
  type: LoadBalancer
  ports:
  - port: 80
    targetPort: 8000
  selector:
    app: api
```

Deploy to Kubernetes:
```bash
kubectl apply -f k8s/
kubectl get pods
kubectl logs -f deployment/grandma-scraper-api
```

### Option 3: Cloud Platforms

#### AWS (Elastic Beanstalk)
```bash
# Install EB CLI
pip install awsebcli

# Initialize EB application
eb init -p python-3.11 grandma-scraper

# Create environment
eb create production

# Deploy
eb deploy
```

#### Heroku
```bash
# Install Heroku CLI and login
heroku login

# Create app
heroku create grandma-scraper-prod

# Add PostgreSQL
heroku addons:create heroku-postgresql:standard-0

# Add Redis
heroku addons:create heroku-redis:premium-0

# Set environment variables
heroku config:set SECRET_KEY=$(openssl rand -hex 32)

# Deploy
git push heroku main

# Scale workers
heroku ps:scale web=2 worker=3
```

---

## Environment Variables

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `POSTGRES_USER` | Database username | `grandma_scraper` |
| `POSTGRES_PASSWORD` | Database password | `strong_password_here` |
| `POSTGRES_SERVER` | Database host | `localhost` or `postgres` |
| `POSTGRES_PORT` | Database port | `5432` |
| `POSTGRES_DB` | Database name | `grandma_scraper` |
| `SECRET_KEY` | JWT signing key | `openssl rand -hex 32` |
| `CELERY_BROKER_URL` | Redis URL for Celery | `redis://localhost:6379/0` |
| `CELERY_RESULT_BACKEND` | Redis URL for results | `redis://localhost:6379/0` |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ALGORITHM` | JWT algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiry | `30` |
| `CORS_ORIGINS` | Allowed CORS origins | `["*"]` |
| `VITE_API_BASE_URL` | Frontend API URL | `http://localhost:8000/api/v1` |
| `VITE_WS_BASE_URL` | Frontend WebSocket URL | `ws://localhost:8000/api/v1` |

---

## Troubleshooting

### Database Connection Issues

```bash
# Check if PostgreSQL is running
docker ps | grep postgres

# Test connection
psql -h localhost -U grandma_scraper -d grandma_scraper

# Check logs
docker logs grandma-postgres
```

### Celery Worker Issues

```bash
# Check Celery logs
docker-compose logs -f celery_worker

# Test Redis connection
redis-cli ping

# Manually run a task
python -c "from grandma_scraper.tasks.scrape import run_scrape_task; run_scrape_task.delay('job_id', 'result_id')"
```

### Frontend Build Issues

```bash
# Clear cache and rebuild
cd ui/grandma-scraper-ui
rm -rf node_modules package-lock.json
npm install
npm run build

# Check for TypeScript errors
npm run type-check
```

### Port Conflicts

```bash
# Find process using port 8000
lsof -i :8000

# Kill process
kill -9 <PID>

# Use different port
uvicorn grandma_scraper.api.main:app --port 8001
```

### Performance Issues

**Increase Celery workers:**
```bash
docker-compose up -d --scale celery_worker=5
```

**Database connection pooling:**
```python
# In database config
engine = create_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True
)
```

**Enable caching:**
```bash
# Add Redis cache in addition to task queue
docker run -d --name cache-redis -p 6380:6379 redis:7-alpine
```

---

## Security Best Practices

1. **Never commit secrets to git**
   ```bash
   # Add to .gitignore
   echo ".env*" >> .gitignore
   echo "*.pem" >> .gitignore
   ```

2. **Use strong passwords**
   ```bash
   # Generate secure passwords
   openssl rand -base64 32
   ```

3. **Enable HTTPS in production**
   - Use nginx or Caddy as reverse proxy
   - Get SSL certificates from Let's Encrypt

4. **Limit CORS origins**
   ```python
   # In main.py
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["https://yourdomain.com"],  # Not ["*"]
       allow_credentials=True,
       allow_methods=["GET", "POST", "PUT", "DELETE"],
       allow_headers=["*"],
   )
   ```

5. **Set up rate limiting**
   ```bash
   pip install slowapi
   ```

6. **Regular backups**
   ```bash
   # Backup PostgreSQL
   docker exec grandma-postgres pg_dump -U grandma_scraper grandma_scraper > backup.sql

   # Restore
   docker exec -i grandma-postgres psql -U grandma_scraper grandma_scraper < backup.sql
   ```

---

## Monitoring

### Health Checks

```bash
# API health
curl http://localhost:8000/api/v1/health

# Database health
docker exec grandma-postgres pg_isready

# Redis health
docker exec grandma-redis redis-cli ping
```

### Logging

Set up centralized logging with ELK stack or Cloud Watch.

### Metrics

Add Prometheus metrics:
```bash
pip install prometheus-fastapi-instrumentator
```

---

## Support

For issues and questions:
- GitHub Issues: https://github.com/yourusername/grandma-scraper/issues
- Documentation: https://docs.grandmascraper.com
- Discord: https://discord.gg/grandmascraper
