# 🗺️ Playwright Execution Farm - Roadmap

## What We're Building

A **distributed test execution platform** that:
- Runs Playwright tests remotely
- Streams live logs to a dashboard
- Scales to multiple workers
- Deploys to Railway
- Supports multiple browsers/devices

---

## Phase 1: Basic MVP (Steps 1-7) ← YOU ARE HERE

### Architecture
```
Your Computer
   │
   ├── FastAPI API (http://127.0.0.1:8000)
   │   ├── GET /      (health check)
   │   └── POST /run  (execute test)
   │
   └── Pytest Worker
       └── tests/test_demo.py (fake test, no browser yet)
```

### What It Does
- API accepts a `/run` request
- Spawns a subprocess to run pytest
- Waits for it to complete
- Returns exit code

### Files Created
- `api/main.py` — FastAPI server
- `worker/runner.py` — Pytest executor
- `tests/test_demo.py` — Fake test
- `requirements.txt` — Dependencies

### ✅ Success Criteria
```
POST /run → {"status": "completed", "exit_code": 0}
```

---

## Phase 2: Live Execution Feed (WebSocket) ← NEXT

### Architecture
```
Dashboard (Browser)
   │
   ├──────────────────┐
   │                  │ WebSocket
   │                  ▼
   │           FastAPI API
   │                  │
   │           POST /run
   │                  │
   │                  ▼
   │           Job #abc123
   │                  │
   └─ live events ◄─ │
       (logs,       Pytest
        status)     Worker
```

### New Endpoints
- `POST /run` → returns `job_id`
- `GET /jobs/{job_id}` → fetch job status + logs
- `WebSocket /ws/{job_id}` → stream live events

### New Files
- `worker/job_manager.py` — Job queue
- `api/dashboard.html` — Browser dashboard

### Event Flow
```
POST /run
   ↓
Job #123 returned
   ↓
Connect WebSocket /ws/123
   ↓
JOB_STARTED
   ↓
Opening application...
   ↓
Entering username...
   ↓
... (live logs)
   ↓
JOB_PASSED
   ↓
WebSocket closes
```

### ✅ Success Criteria
Open dashboard, click "Run Test", watch logs appear **live** as the test runs.

---

## Phase 3: ZIP Upload

### Add
- `POST /upload` — accept .zip file
- Extract tests from ZIP
- Run them with POST /run

### Files
- `api/upload_handler.py`
- `uploads/` directory

### ✅ Success Criteria
Upload `my-tests.zip` → Extract and run tests → See results.

---

## Phase 4: Docker Worker

### Why
- Encapsulate all dependencies
- Easy to deploy to Railway
- Reproducible environment

### Add
- `Dockerfile`
- `docker-compose.yml`

### ✅ Success Criteria
```bash
docker build -t playwright-farm .
docker run -p 8000:8000 playwright-farm
```

Works the same as local.

---

## Phase 5: Railway Deployment

### Why
- Free/cheap hosting
- Automatic scaling
- Easy to scale workers

### Add
- `railway.json`
- Environment variables
- Cloud storage for results

### ✅ Success Criteria
```
https://my-app.railway.app/docs
```

Runs in the cloud.

---

## Phase 6: Multiple Workers

### Architecture
```
Dashboard
   │
   └─ Load Balancer
       │
       ├─ Worker 1
       ├─ Worker 2
       ├─ Worker 3
       └─ Worker N
```

### Add
- Worker registration
- Job queue (Redis)
- Load balancing

### ✅ Success Criteria
Submit 10 tests → Run 3 in parallel → See all results.

---

## Phase 7: Browser Matrix

### Run tests on
- Chrome
- Firefox
- Safari
- Mobile Chrome
- Mobile Safari

### Add
- Matrix config (YAML)
- Parallel Playwright launchers

### ✅ Success Criteria
One test → Runs on 5 browsers automatically → Reports per browser.

---

## Phase 8: Reports & Traces

### Add
- Screenshots (every step)
- Playwright traces (debug video)
- Allure reports
- HTML reports

### Files
- `results/` directory
- Report generator

### ✅ Success Criteria
Download `.zip` with HTML reports + screenshots + traces.

---

## Phase 9: Private Network Access

### Support
- Tunnel to private UAT
- VPN integration
- Firewall bypass

### Add
- Cloudflare Tunnel
- SSH tunneling

### ✅ Success Criteria
Run tests against internal `http://internal-uat:8080`.

---

## Phase 10: Multi-Tenant SaaS

### Support
- User accounts
- Workspaces
- Billing
- API keys

### Add
- PostgreSQL
- Authentication
- Stripe integration

### ✅ Success Criteria
Multiple users → Isolated workspaces → Pay per test run.

---

## Current Status

### ✅ Phase 1: READY TO TEST
All files created. You just need to:
1. Copy to your computer
2. Run `setup.sh` or `setup.bat`
3. Start the server
4. Test with FastAPI docs
5. Tell me "Step 1 done"

### ⏳ Phase 2-10: WAITING FOR YOUR SIGNAL
Once Phase 1 works, I'll build:
- WebSocket live feed
- Job tracking
- Dashboard
- File upload
- Docker
- Railway
- Scaling
- Reports
- Everything else

---

## Key Files Summary

### Phase 1 (NOW)
```
api/main.py           ← FastAPI server with /run endpoint
worker/runner.py      ← Pytest subprocess executor
tests/test_demo.py    ← Fake test (no browser yet)
requirements.txt      ← Dependencies
setup.sh / setup.bat  ← Quick setup scripts
```

### Phase 2 (NEXT)
```
worker/job_manager.py ← Job tracking + event broadcasting
api/main.py           ← Add WebSocket /ws/{job_id}
api/dashboard.html    ← Browser UI with WebSocket client
```

### Phase 3+
```
api/upload_handler.py ← ZIP file upload
Dockerfile            ← Container image
railway.json          ← Railway config
worker/queue.py       ← Job queue (Redis)
```

---

## Your Next Move

1. **Follow QUICKSTART.md** (10 minutes)
2. **Get `exit_code: 0`**
3. **Tell me "Step 1 done"**
4. **I'll build Phase 2** (live WebSocket feed)

Let's go! 🚀
