# 🚀 Quick Start - V2-V10 Complete System

All phases are **ready to use**. No additional setup needed beyond Phase 1.

## 60-Second Start

### 1. You Already Have Phase 1
```bash
cd playwright-farm
# Your existing setup from V1 is ready
```

### 2. Start with Docker (Recommended)
```bash
docker-compose up
```

**That's it!** You now have:
- ✅ API running (http://localhost:8000)
- ✅ PostgreSQL database (localhost:5432)
- ✅ Redis cache (localhost:6379)
- ✅ Dashboard (http://localhost:8000)

### 3. Open Dashboard
```
http://localhost:8000
```

---

## What's Available

### In Dashboard (No API calls needed)

| Tab | What It Does | Phase |
|-----|--------------|-------|
| **Jobs** | View/manage all tests | V2 |
| **New Job** | Create tests or upload ZIP | V2 |
| **Live Logs** | Real-time execution streaming | V2 |
| **Workers** | View registered workers | V6 |
| **Browser Matrix** | Multi-browser testing | V7 |

### Via API

```bash
# V2: Create job
curl -X POST http://localhost:8000/jobs?test_file=test_demo.py

# V2: Stream logs
wscat -c ws://localhost:8000/ws/{job_id}

# V2: Upload ZIP
curl -F "file=@tests.zip" http://localhost:8000/upload

# V6: Register worker
curl -X POST http://localhost:8000/workers \
  -d "name=worker1&provider=docker&endpoint=http://worker:8000"

# V5: Create tunnel
curl -X POST http://localhost:8000/tunnels \
  -d "name=UAT&local_host=internal-uat&local_port=8080"

# V7: Matrix job
curl -X POST http://localhost:8000/jobs/matrix \
  -d "test_file=test_login.py&browsers=chrome&browsers=firefox&devices=desktop&devices=mobile"

# V10: Create workspace
curl -X POST http://localhost:8000/workspaces \
  -d "name=MyTeam&owner_id=user123"
```

---

## Common Tasks

### Upload Tests (V2)

1. Open Dashboard
2. Go to "New Job" tab
3. Click "📁 Upload Test ZIP"
4. Select your `tests.zip`
5. Done! Tests extracted and ready

### Run Test Across Browsers (V7)

Dashboard → Browser Matrix tab:
1. Select: Chrome, Firefox, Safari
2. Select: Desktop, Mobile, Tablet
3. Click "Run Matrix Test"
4. Watch 9 jobs run in parallel

### Register Docker Worker (V6)

```bash
# Start worker container
docker run -p 8001:8000 execution-farm:latest

# Register it
curl -X POST http://localhost:8000/workers \
  -d "name=docker-worker-1&provider=docker&endpoint=http://localhost:8001"

# Now jobs automatically distribute across workers
```

### Access Private UAT (V5)

```bash
# Start tunnel to internal server
curl -X POST http://localhost:8000/tunnels \
  -d "name=MyUAT&local_host=internal.company.com&local_port=8080"

# Response includes public URL:
# "public_url": "https://tunnel-abc123-public.tunnel.dev"

# Now your tests can access the private server
```

---

## Environment Setup

### Using Docker Compose (Easiest)

```bash
docker-compose up
```

Already includes:
- API with all V2-V10 features
- PostgreSQL (auto-initialized)
- Redis (auto-started)
- Proper networking

### Manual Setup

```bash
# Copy env template
cp .env.example .env

# Install dependencies
pip install -r requirements.txt

# Start services separately
redis-server &
postgres -D /path/to/data &
uvicorn api.main:app --reload
```

---

## API Endpoints Quick Reference

### Jobs Management (V2)
```
POST   /jobs                    Create job
GET    /jobs                    List jobs
GET    /jobs/{id}               Get job details
POST   /jobs/{id}/cancel        Cancel job
WS     /ws/{id}                 Stream logs
```

### File Upload (V2)
```
POST   /upload                  Upload ZIP
```

### Worker Pool (V6)
```
GET    /workers                 List all workers
POST   /workers                 Register worker
GET    /pools                   List pools
POST   /pools                   Create pool
GET    /pools/{id}              Pool stats
POST   /pools/{id}/workers      Add worker
```

### Tunnels (V5)
```
POST   /tunnels                 Create tunnel
GET    /tunnels                 List tunnels
GET    /tunnels/{id}            Tunnel details
DELETE /tunnels/{id}            Delete tunnel
POST   /tunnel-config           Set provider
GET    /tunnel-config           Get config
```

### Browser Matrix (V7)
```
POST   /jobs/matrix             Run matrix job
```

### Reports (V8)
```
GET    /jobs/{id}/report        Get report
POST   /jobs/{id}/screenshots   Upload screenshot
```

### Multi-Tenant (V10)
```
POST   /workspaces              Create workspace
GET    /workspaces/{id}/jobs    Workspace jobs
GET    /workspaces/{id}/billing Billing info
```

### Dashboard
```
GET    /dashboard               UI
GET    /dashboard/summary       Stats
GET    /api/version             Version info
```

---

## Features by Phase

### ✅ V2: WebSocket + ZIP
- Real-time log streaming
- ZIP file extraction
- Job tracking & cancellation

### ✅ V3: Docker
- Containerized deployment
- `docker-compose.yml` ready
- Services: API, DB, Redis

### ✅ V4: Railway
- `railway.json` configured
- One-command deploy
- Auto-scaling

### ✅ V5: Tunnel
- Private network access
- Multiple providers (Cloudflare, ngrok, SSH)
- VPN support

### ✅ V6: Workers
- Worker registration
- Pool management
- Auto load-balancing

### ✅ V7: Browser Matrix
- Multi-browser execution
- Multiple device types
- Parallel runs

### ✅ V8: Reports
- Screenshot support
- Allure reports
- Trace recording

### ✅ V10: Multi-Tenant
- Workspace isolation
- User authentication
- Billing tracking

---

## Verification Checklist

After starting, verify:

```bash
# Dashboard loads
curl -I http://localhost:8000
# Expected: 200 OK

# Create test job
curl -X POST http://localhost:8000/jobs?test_file=test_demo.py
# Expected: {"job_id": "..."}

# List workers
curl http://localhost:8000/workers
# Expected: {"workers": [...]}

# Check version
curl http://localhost:8000/api/version
# Expected: {"version": "2.0", "phases": {...}}
```

---

## Troubleshooting

### Port already in use
```bash
# Use different port
uvicorn api.main:app --port 8001

# Or kill existing process
lsof -ti:8000 | xargs kill -9
```

### Database connection error
```bash
# Check DATABASE_URL
echo $DATABASE_URL

# Verify PostgreSQL is running
psql -U postgres -c "SELECT 1"
```

### WebSocket connection fails
```bash
# Check firewall
curl -v http://localhost:8000

# Use ngrok for external access
ngrok http 8000
```

### Docker build fails
```bash
# Clear cache
docker-compose build --no-cache

# Check Dockerfile
cat Dockerfile
```

---

## Next: Deploy to Production

When ready, follow `DEPLOY.md`:

1. Setup Railway account
2. Run `railway login`
3. Run `railway up`
4. Done!

App is live at: `https://your-app.railway.app`

---

## File Structure Reminder

```
playwright-farm/
├── api/
│   ├── main.py           ← All V2-V10 endpoints
│   ├── dashboard.html    ← React UI
│   ├── models.py         ← Database models
│   ├── upload_handler.py ← V2
│   └── tunnel_manager.py ← V5
│
├── worker/
│   ├── runner.py         ← Executor
│   ├── job_manager.py    ← V2 WebSocket
│   └── pool_manager.py   ← V6 Workers
│
├── Dockerfile            ← V3
├── docker-compose.yml    ← Local dev
├── railway.json          ← V4
├── requirements.txt      ← All deps
└── COMPLETE_GUIDE.md     ← Full docs
```

---

## Support Files

- **COMPLETE_GUIDE.md** — In-depth explanation of all features
- **DEPLOY.md** — Deployment instructions
- **.env.example** — Environment variables
- **ROADMAP.md** — Original roadmap

---

## Success = This Works

1. ✅ Dashboard loads at http://localhost:8000
2. ✅ Create job, see live logs
3. ✅ Upload ZIP with tests
4. ✅ Register Docker worker
5. ✅ Run matrix job (3 browsers × 2 devices)
6. ✅ Access tunnel to private server

**You have a complete enterprise test platform!**

---

## TL;DR

```bash
# Start
docker-compose up

# Open
http://localhost:8000

# Create job
Dashboard → New Job → Run Test

# Done!
# Everything from V2-V10 ready to use
```

🚀 **Go build!**
