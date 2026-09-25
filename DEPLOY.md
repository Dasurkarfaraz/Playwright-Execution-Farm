# 🚀 Deployment Guide - V3-V10

## Quick Deploy Checklist

- [ ] Update requirements.txt dependencies
- [ ] Set environment variables
- [ ] Test locally with docker-compose
- [ ] Deploy to Railway

---

## Local Development (V3 - Docker)

### Start Everything
```bash
docker-compose up
```

This starts:
- **API** (port 8000)
- **PostgreSQL** (port 5432)
- **Redis** (port 6379)

### Access
```
Dashboard:    http://localhost:8000
API Docs:     http://localhost:8000/docs
PostgreSQL:   localhost:5432 (user: playwright, pass: playwright123)
Redis:        localhost:6379
```

### Stop
```bash
docker-compose down
```

### Rebuild
```bash
docker-compose up --build
```

---

## Railway Deployment (V4)

### 1. Install Railway CLI
```bash
npm install -g @railway/cli
```

### 2. Login
```bash
railway login
```

### 3. Create Project
```bash
railway init
```

### 4. Deploy
```bash
railway up
```

### 5. Check Status
```bash
railway status
```

### 6. View Logs
```bash
railway logs
```

### Environment Variables on Railway

Set these in Railway console:

```env
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
SECRET_KEY=your-generated-secret
ENVIRONMENT=production
```

---

## Production Checklist

### Security
- [ ] Change all default passwords
- [ ] Enable HTTPS/TLS
- [ ] Set strong SECRET_KEY
- [ ] Enable authentication
- [ ] Setup API keys

### Performance
- [ ] Configure worker pool size
- [ ] Setup load balancer
- [ ] Enable caching (Redis)
- [ ] Configure CDN

### Monitoring
- [ ] Setup logging (Sentry/LogRocket)
- [ ] Monitor worker health
- [ ] Track job performance
- [ ] Setup alerts

### Backup
- [ ] Database backups
- [ ] Configuration backups
- [ ] Test restore procedure

---

## Worker Setup (V6)

### Local Docker Worker

**1. Create worker container**
```dockerfile
# worker/Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
RUN playwright install chromium
COPY . .
CMD ["python", "-m", "worker.standalone"]
```

**2. Run worker**
```bash
docker run -e API_URL=http://api:8000 execution-farm-worker:latest
```

**3. Register in pool**
```bash
curl -X POST http://localhost:8000/workers \
  -d "name=docker-worker-1&provider=docker&endpoint=http://worker:8000"
```

### Railway Worker

**1. Deploy separate instance on Railway**
```bash
railway up --service worker
```

**2. Register
```bash
curl -X POST http://api.railway.app/workers \
  -d "name=railway-worker-1&provider=railway&endpoint=https://worker.railway.app"
```

### AWS Lambda Worker (Serverless)

```python
# worker/lambda_handler.py
import json
from worker.job_manager import job_manager

def handler(event, context):
    test_file = event.get('test_file')
    job_id = job_manager.create_job(test_file)
    
    return {
        'statusCode': 200,
        'body': json.dumps({'job_id': job_id})
    }
```

Deploy to AWS Lambda and register:
```bash
curl -X POST http://localhost:8000/workers \
  -d "name=lambda-worker&provider=lambda&endpoint=https://lambda-url.com"
```

---

## Private Network Access (V5)

### Cloudflare Tunnel Setup

**1. Install cloudflared**
```bash
wget https://github.com/cloudflare/cloudflared/releases/download/2024.1.5/cloudflared-linux-amd64
chmod +x cloudflared-linux-amd64
```

**2. Authenticate**
```bash
./cloudflared-linux-amd64 tunnel login
```

**3. Create tunnel**
```bash
./cloudflared-linux-amd64 tunnel create my-uat-tunnel
```

**4. Configure**
```bash
curl -X POST http://localhost:8000/tunnels \
  -d "name=UAT&local_host=internal-uat&local_port=8080"
```

**5. Start**
```bash
./cloudflared-linux-amd64 tunnel run my-uat-tunnel
```

### ngrok Alternative

```bash
# Install
brew install ngrok

# Create account
ngrok config add-authtoken YOUR_TOKEN

# Expose local service
ngrok http http://internal-uat:8080

# Register with API
curl -X POST http://localhost:8000/tunnels \
  -d "name=UAT&local_host=internal-uat&local_port=8080"
```

---

## Database Setup

### PostgreSQL

**1. Run migrations**
```bash
alembic upgrade head
```

**2. Create superuser**
```python
from api.models import User
from sqlalchemy.orm import Session

user = User(
    id="admin",
    email="admin@company.com",
    hashed_password="...",
    is_active=True
)
db.add(user)
db.commit()
```

### Redis

For caching and job queues:
```bash
# Local
redis-server

# Docker
docker run -p 6379:6379 redis:7-alpine

# Production
# Use managed Redis (Railway, AWS ElastiCache, etc.)
```

---

## Monitoring & Logging

### Sentry (Error Tracking)

```python
import sentry_sdk

sentry_sdk.init(
    dsn="https://key@sentry.io/project",
    environment="production",
    traces_sample_rate=0.1
)
```

### Prometheus (Metrics)

```python
from prometheus_client import Counter, Histogram

job_counter = Counter('jobs_total', 'Total jobs')
job_duration = Histogram('job_duration_seconds', 'Job duration')
```

### Logging

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)
```

---

## Scaling Strategy

### Phase 1: Single Server
- 1 API instance
- 1-2 workers
- Shared database

### Phase 2: Worker Pool
- 1 API instance
- 5-10 Docker workers
- Dedicated database

### Phase 3: Distributed
- Load-balanced API (3+)
- Auto-scaling workers (10-50)
- Database cluster
- Redis cluster

### Phase 4: Global
- Multi-region deployment
- Geographic load balancing
- Regional databases
- Global reporting

---

## Troubleshooting

### Deploy Fails

**Check logs**
```bash
railway logs
```

**Common issues:**
- Missing environment variables
- Database connection failed
- Worker image not found

### Slow Performance

**Check:**
```bash
# Worker utilization
curl http://api/workers

# Pool stats
curl http://api/pools

# Recent jobs
curl http://api/jobs
```

**Optimize:**
- Add more workers
- Increase database connections
- Enable Redis caching

### Database Connection Error

**Fix:**
```bash
# Verify DATABASE_URL
echo $DATABASE_URL

# Test connection
psql $DATABASE_URL -c "SELECT 1"
```

---

## Success Indicators

✅ Dashboard loads at http://app.railway.app  
✅ Can create jobs  
✅ WebSocket logs stream  
✅ Workers auto-register  
✅ Tests run across pool  
✅ Reports generate  
✅ No 500 errors  

---

## Next Level

Once V4 is running:

1. **Add billing** (Stripe/Paddle)
2. **User authentication** (JWT)
3. **API rate limiting**
4. **Custom domain** (CNAME)
5. **SSL certificate** (Let's Encrypt)
6. **CDN** (Cloudflare)
7. **Monitoring** (Datadog/New Relic)
8. **Backup** (nightly PostgreSQL dumps)

---

## Support

Check logs:
```bash
# Local
docker-compose logs -f api

# Railway
railway logs --follow

# Errors
grep ERROR logs/*.log
```

Debug mode:
```bash
export DEBUG=1
uvicorn api.main:app --reload --log-level debug
```

---

**You're ready to deploy!** 🚀
