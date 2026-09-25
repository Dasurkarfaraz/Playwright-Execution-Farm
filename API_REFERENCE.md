# API Reference - Complete V2-V10

All endpoints documented with examples. Start server first:

```bash
docker-compose up
# API available at http://localhost:8000
```

---

## Base URL
```
http://localhost:8000
```

---

## Authentication

Not implemented yet (V10). For production, add JWT:

```bash
# Get token
curl -X POST http://localhost:8000/auth/login \
  -d "email=user@example.com&password=password"

# Use token
curl -H "Authorization: Bearer {token}" \
  http://localhost:8000/jobs
```

---

## Response Format

### Success (200)
```json
{
  "data": {...},
  "status": "success"
}
```

### Error (4xx, 5xx)
```json
{
  "error": "Description",
  "status": "error",
  "code": "ERROR_CODE"
}
```

---

## Jobs Management (V2)

### Create Job
```http
POST /jobs
```

**Parameters:**
```json
{
  "test_file": "test_demo.py",
  "user_id": "user123"
}
```

**Response:**
```json
{
  "job_id": "abc-123-def",
  "status": "queued",
  "test_file": "test_demo.py"
}
```

**Example:**
```bash
curl -X POST "http://localhost:8000/jobs?test_file=test_demo.py"
```

### List Jobs
```http
GET /jobs
```

**Parameters:**
- `user_id` (optional) — Filter by user

**Response:**
```json
{
  "jobs": [
    {
      "id": "job-1",
      "status": "passed",
      "test_file": "test_demo.py",
      "exit_code": 0,
      "created_at": "2024-09-25T00:00:00Z",
      "completed_at": "2024-09-25T00:01:00Z"
    }
  ]
}
```

**Example:**
```bash
curl "http://localhost:8000/jobs"
curl "http://localhost:8000/jobs?user_id=user123"
```

### Get Job Details
```http
GET /jobs/{job_id}
```

**Response:**
```json
{
  "id": "job-1",
  "status": "running",
  "logs": ["Opening application...", "Entering username..."],
  "screenshots": [],
  "traces": [],
  "exit_code": null,
  "created_at": "2024-09-25T00:00:00Z",
  "started_at": "2024-09-25T00:00:01Z",
  "completed_at": null,
  "user_id": "user123"
}
```

**Example:**
```bash
curl "http://localhost:8000/jobs/abc-123-def"
```

### Cancel Job
```http
POST /jobs/{job_id}/cancel
```

**Response:**
```json
{
  "status": "cancelled"
}
```

**Example:**
```bash
curl -X POST "http://localhost:8000/jobs/abc-123-def/cancel"
```

### Live Log Stream
```http
WebSocket /ws/{job_id}
```

**Connect:**
```bash
wscat -c ws://localhost:8000/ws/abc-123-def
```

**Receives:**
```json
{"type":"log","message":"Opening application...","timestamp":"2024-09-25T00:00:01Z"}
{"type":"log","message":"Login successful","timestamp":"2024-09-25T00:00:05Z"}
{"type":"job_passed","job_id":"job-1","exit_code":0,"duration":4.5}
```

**JavaScript:**
```javascript
const ws = new WebSocket("ws://localhost:8000/ws/job-id");
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data);
};
```

---

## File Upload (V2)

### Upload ZIP File
```http
POST /upload
```

**Content-Type:** `multipart/form-data`

**Body:**
- `file` — ZIP file

**Response:**
```json
{
  "upload_id": "upload-123",
  "extract_path": "/tmp/extracted/abc123",
  "test_files": [
    "tests/test_login.py",
    "tests/test_checkout.py"
  ],
  "count": 2
}
```

**Example:**
```bash
curl -F "file=@tests.zip" http://localhost:8000/upload
```

**Python:**
```python
import requests

with open("tests.zip", "rb") as f:
    files = {"file": f}
    response = requests.post("http://localhost:8000/upload", files=files)
    print(response.json())
```

---

## Worker Management (V6)

### List Workers
```http
GET /workers
```

**Response:**
```json
{
  "workers": [
    {
      "id": "worker-1",
      "name": "Local Worker",
      "provider": "local",
      "endpoint": "http://127.0.0.1:8000",
      "status": "online",
      "current_jobs": 2,
      "max_jobs": 3,
      "cpu_cores": 4,
      "memory_gb": 8,
      "success_rate": 98.5
    }
  ]
}
```

**Example:**
```bash
curl http://localhost:8000/workers
```

### Register Worker
```http
POST /workers
```

**Parameters:**
```json
{
  "name": "docker-worker-1",
  "provider": "docker",
  "endpoint": "http://worker1:8000"
}
```

**Response:**
```json
{
  "worker_id": "worker-abc123",
  "status": "registered",
  "name": "docker-worker-1",
  "provider": "docker",
  "endpoint": "http://worker1:8000"
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/workers \
  -d "name=docker-worker-1&provider=docker&endpoint=http://worker:8000"
```

### List Pools
```http
GET /pools
```

**Response:**
```json
{
  "pools": [
    {
      "pool_id": "pool-default",
      "pool_name": "Default Pool",
      "total_workers": 5,
      "online_workers": 4,
      "total_capacity": 15,
      "used_capacity": 3,
      "available_slots": 12,
      "utilization": 20.0
    }
  ]
}
```

### Create Pool
```http
POST /pools
```

**Parameters:**
```json
{
  "name": "Production Pool",
  "min_workers": 2,
  "max_workers": 10
}
```

**Response:**
```json
{
  "pool_id": "pool-prod-123",
  "name": "Production Pool",
  "status": "created"
}
```

### Get Pool Stats
```http
GET /pools/{pool_id}
```

**Response:**
```json
{
  "pool_id": "pool-default",
  "total_workers": 5,
  "online_workers": 4,
  "utilization": 20.0
}
```

### Add Worker to Pool
```http
POST /pools/{pool_id}/workers
```

**Parameters:**
```json
{
  "name": "new-worker",
  "provider": "railway",
  "endpoint": "https://worker.railway.app"
}
```

**Response:**
```json
{
  "worker_id": "worker-xyz",
  "pool_id": "pool-default",
  "status": "added"
}
```

---

## Tunnels (V5)

### Create Tunnel
```http
POST /tunnels
```

**Parameters:**
```json
{
  "name": "UAT Server",
  "local_host": "internal-uat.company.com",
  "local_port": 8080
}
```

**Response:**
```json
{
  "id": "tunnel-abc123",
  "name": "UAT Server",
  "status": "active",
  "local": "internal-uat.company.com:8080",
  "private_url": "https://tunnel-abc123.tunnel.local",
  "public_url": "https://tunnel-abc123-public.tunnel.dev",
  "created_at": "2024-09-25T00:00:00Z",
  "bandwidth_used": 0
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/tunnels \
  -d "name=UAT&local_host=internal-uat&local_port=8080"
```

### List Tunnels
```http
GET /tunnels
```

**Response:**
```json
{
  "tunnels": [
    {
      "id": "tunnel-1",
      "name": "UAT Server",
      "status": "active",
      "local": "internal-uat:8080",
      "public_url": "https://..."
    }
  ]
}
```

### Delete Tunnel
```http
DELETE /tunnels/{tunnel_id}
```

**Response:**
```json
{
  "status": "deleted"
}
```

### Set Tunnel Provider
```http
POST /tunnel-config
```

**Parameters:**
```json
{
  "provider": "cloudflare",
  "auth_token": "your-token"
}
```

**Response:**
```json
{
  "status": "configured",
  "provider": "cloudflare"
}
```

---

## Browser Matrix (V7)

### Create Matrix Job
```http
POST /jobs/matrix
```

**Parameters:**
```json
{
  "test_file": "test_login.py",
  "browsers": ["chrome", "firefox", "safari"],
  "devices": ["desktop", "mobile", "tablet"]
}
```

**Response:**
```json
{
  "matrix_id": "matrix-abc123",
  "jobs": [
    {
      "job_id": "job-1",
      "browser": "chrome",
      "device": "desktop"
    },
    {
      "job_id": "job-2",
      "browser": "chrome",
      "device": "mobile"
    }
  ],
  "total": 9
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/jobs/matrix \
  -H "Content-Type: application/json" \
  -d '{
    "test_file": "test_login.py",
    "browsers": ["chrome", "firefox"],
    "devices": ["desktop", "mobile"]
  }'
```

---

## Reports (V8)

### Get Job Report
```http
GET /jobs/{job_id}/report
```

**Response:**
```json
{
  "job_id": "job-123",
  "report_type": "allure",
  "screenshots": [
    "https://cdn/screenshot-1.png",
    "https://cdn/screenshot-2.png"
  ],
  "traces": [
    "https://cdn/trace-1.zip"
  ],
  "logs": ["log line 1", "log line 2"]
}
```

### Upload Screenshot
```http
POST /jobs/{job_id}/screenshots
```

**Content-Type:** `multipart/form-data`

**Body:**
- `file` — Image file

**Response:**
```json
{
  "screenshot_id": "screenshot-abc",
  "path": "results/job-123/screenshot.png",
  "size": 123456
}
```

---

## Multi-Tenant (V10)

### Create Workspace
```http
POST /workspaces
```

**Parameters:**
```json
{
  "name": "My Company",
  "owner_id": "user-123"
}
```

**Response:**
```json
{
  "workspace_id": "ws-abc123",
  "name": "My Company",
  "owner_id": "user-123",
  "created_at": "2024-09-25T00:00:00Z"
}
```

### Get Workspace Jobs
```http
GET /workspaces/{workspace_id}/jobs
```

**Response:**
```json
{
  "workspace_id": "ws-123",
  "jobs": [
    {
      "id": "job-1",
      "status": "passed",
      "test_file": "test_login.py"
    }
  ],
  "total": 1
}
```

### Get Workspace Billing
```http
GET /workspaces/{workspace_id}/billing
```

**Response:**
```json
{
  "workspace_id": "ws-123",
  "period": "2024-09",
  "job_count": 100,
  "worker_hours": 50,
  "cost": 150,
  "currency": "USD"
}
```

---

## Dashboard

### Get Dashboard Summary
```http
GET /dashboard/summary
```

**Parameters:**
- `workspace_id` (optional)

**Response:**
```json
{
  "total_jobs": 150,
  "passed": 142,
  "failed": 8,
  "running": 0,
  "success_rate": 94.7
}
```

### Serve Dashboard
```http
GET /dashboard
```

**Returns:** HTML page with React dashboard

---

## System

### Get API Version
```http
GET /api/version
```

**Response:**
```json
{
  "version": "2.0",
  "phases": {
    "1": "Basic MVP",
    "2": "WebSocket + ZIP Upload",
    "3": "Docker Worker",
    "4": "Railway Deployment",
    "5": "Tunnel to Private UAT",
    "6": "Multiple Workers",
    "7": "Browser/Device Matrix",
    "8": "Allure + Traces + Screenshots",
    "9": "Free/Cheap Worker Providers",
    "10": "Multi-Tenant SaaS"
  }
}
```

### Health Check
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy"
}
```

---

## Rate Limiting

Not implemented yet. Each endpoint has no limits locally.

For production, add:
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1234567890
```

---

## Pagination

Not implemented yet. For large lists, add pagination:

```http
GET /jobs?skip=0&limit=50
```

---

## Sorting

Query endpoints support sorting:

```http
GET /jobs?sort=created_at:desc
GET /jobs?sort=status:asc
```

---

## Filtering

List endpoints support filtering:

```http
GET /jobs?status=passed
GET /jobs?status=failed
GET /jobs?user_id=user123
```

---

## Common Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 400 | Bad request |
| 404 | Not found |
| 500 | Server error |

---

## Error Codes

| Code | Meaning |
|------|---------|
| `JOB_NOT_FOUND` | Job doesn't exist |
| `WORKER_NOT_FOUND` | Worker doesn't exist |
| `INVALID_FILE` | Bad ZIP file |
| `DATABASE_ERROR` | Database issue |
| `WORKER_OFFLINE` | Worker not available |

---

## Examples

### Create and Monitor Job

```bash
# Create job
JOB_ID=$(curl -s -X POST http://localhost:8000/jobs \
  -d "test_file=test_demo.py" | jq -r .job_id)

# Stream logs
wscat -c ws://localhost:8000/ws/$JOB_ID

# In another terminal, get status
curl http://localhost:8000/jobs/$JOB_ID | jq .status
```

### Upload Tests and Run

```bash
# Upload ZIP
RESULT=$(curl -s -F "file=@tests.zip" http://localhost:8000/upload)
TEST_FILE=$(echo $RESULT | jq -r '.test_files[0]')

# Run the test
curl -s -X POST "http://localhost:8000/jobs?test_file=$TEST_FILE"
```

### Register Workers and Check Pool

```bash
# Register docker worker
curl -s -X POST http://localhost:8000/workers \
  -d "name=worker1&provider=docker&endpoint=http://worker:8000"

# Check pool utilization
curl -s http://localhost:8000/pools/pool-default | jq .utilization
```

---

## SDKs & Libraries

### Python Client
```python
import requests
from websockets import connect

BASE = "http://localhost:8000"

# Create job
resp = requests.post(f"{BASE}/jobs", params={"test_file": "test.py"})
job_id = resp.json()["job_id"]

# Get status
resp = requests.get(f"{BASE}/jobs/{job_id}")
print(resp.json()["status"])

# Stream logs
async def stream_logs():
    async with connect(f"ws://localhost:8000/ws/{job_id}") as ws:
        async for msg in ws:
            print(msg)
```

### JavaScript/Node
```javascript
const BASE = "http://localhost:8000";

// Create job
const res = await fetch(`${BASE}/jobs`, { method: "POST" });
const { job_id } = await res.json();

// Stream logs
const ws = new WebSocket(`ws://localhost:8000/ws/${job_id}`);
ws.onmessage = (e) => console.log(e.data);
```

---

## Webhooks

Not implemented yet. For production, add:

```bash
curl -X POST http://localhost:8000/jobs \
  -d "webhook_url=https://myapp.com/job-update"

# Server will POST:
{
  "job_id": "...",
  "status": "passed",
  "timestamp": "2024-09-25T00:00:00Z"
}
```

---

## Documentation

For more details, see:
- **COMPLETE_GUIDE.md** — Full feature explanation
- **QUICKSTART_V2_V10.md** — Quick start guide
- **DEPLOY.md** — Deployment guide

---

**Ready to build!** 🚀
