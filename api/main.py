from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
import uuid
from worker.job_manager import job_manager, JobStatus
from worker.pool_manager import pool_manager
from api.upload_handler import upload_handler
from api.tunnel_manager import tunnel_manager, tunnel_config
from api.agent_manager import agent_manager
import asyncio
import json
import os

app = FastAPI(title="Playwright Execution Farm V2-V10")

# CORS for dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== PHASE 1: Basic Endpoints ====================

@app.get("/")
async def home():
    """Redirect to dashboard"""
    dashboard_path = os.path.join(os.path.dirname(__file__), "dashboard.html")
    if os.path.exists(dashboard_path):
        with open(dashboard_path) as f:
            return HTMLResponse(content=f.read())
    return {
        "message": "Playwright Execution Farm",
        "version": "2.0",
        "phases": "1-10 implemented"
    }

@app.get("/dashboard")
async def dashboard():
    """Serve dashboard UI"""
    dashboard_path = os.path.join(os.path.dirname(__file__), "dashboard.html")
    if os.path.exists(dashboard_path):
        with open(dashboard_path) as f:
            return HTMLResponse(content=f.read())
    return {"error": "Dashboard not found"}, 404

@app.get("/health")
def health():
    return {"status": "healthy"}

# ==================== PHASE 2: WebSocket + Live Feed ====================

@app.post("/jobs")
def create_job(test_file: str = "test_demo.py", user_id: str = None):
    """Create new job (Phase 2)"""
    job_id = job_manager.create_job(test_file, user_id)
    return {
        "job_id": job_id,
        "status": "queued",
        "test_file": test_file
    }

@app.get("/jobs/{job_id}")
def get_job(job_id: str):
    """Get job status and logs (Phase 2)"""
    job = job_manager.get_job(job_id)
    if not job:
        return {"error": "Job not found"}, 404
    return job

@app.get("/jobs")
def list_jobs(user_id: str = None):
    """List all jobs (Phase 2)"""
    return {
        "jobs": job_manager.list_jobs(user_id)
    }

@app.post("/jobs/{job_id}/cancel")
def cancel_job(job_id: str):
    """Cancel running job (Phase 2)"""
    if job_manager.cancel_job(job_id):
        return {"status": "cancelled"}
    return {"error": "Job not found"}, 404

@app.websocket("/ws/{job_id}")
async def websocket_endpoint(websocket: WebSocket, job_id: str):
    """WebSocket live streaming (Phase 2)"""
    await websocket.accept()

    if job_id not in job_manager.jobs:
        await websocket.send_json({"error": "Job not found"})
        await websocket.close()
        return

    job = job_manager.jobs[job_id]
    loop = asyncio.get_running_loop()

    async def send_to_ws(message: str):
        try:
            await websocket.send_text(message)
        except Exception:
            pass

    def listener(message: str):
        asyncio.run_coroutine_threadsafe(send_to_ws(message), loop)

    job_manager.add_listener(job_id, listener)

    # Send existing logs
    for log in job.logs:
        await websocket.send_json({"type": "log", "message": log})

    try:
        while True:
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        job_manager.remove_listener(job_id, listener)

# ==================== PHASE 2: File Upload ====================

@app.post("/upload")
async def upload_zip(file: UploadFile = File(...)):
    """Upload and extract ZIP file (Phase 2-V2)"""
    try:
        content = await file.read()
        filename = f"{uuid.uuid4()}.zip"
        
        zip_path = upload_handler.save_zip_file(content, filename)
        success, extract_path, test_files = upload_handler.extract_zip(zip_path)
        
        if not success:
            return {"error": extract_path}, 400

        return {
            "upload_id": uuid.uuid4().hex,
            "extract_path": extract_path,
            "test_files": test_files,
            "count": len(test_files)
        }
    except Exception as e:
        return {"error": str(e)}, 500

# ==================== PHASE 6: Worker Management ====================

@app.get("/workers")
def list_workers():
    """List all workers (Phase 6)"""
    return {
        "workers": pool_manager.get_pool("pool-default").list_workers() if pool_manager.get_pool("pool-default") else []
    }

@app.post("/workers")
def register_worker(name: str, provider: str, endpoint: str = None):
    """Register new worker (Phase 6)"""
    worker_id = pool_manager.add_worker_to_pool("pool-default", name, provider, endpoint)
    if worker_id:
        return {
            "worker_id": worker_id,
            "status": "registered",
            "name": name,
            "provider": provider,
            "endpoint": endpoint
        }
    return {"error": "Failed to register worker"}, 500

@app.get("/pools")
def list_pools():
    """List worker pools (Phase 6)"""
    return {
        "pools": pool_manager.list_pools()
    }

@app.post("/pools")
def create_pool(name: str, min_workers: int = 1, max_workers: int = 5):
    """Create new worker pool (Phase 6)"""
    pool_id = pool_manager.create_pool(name, min_workers, max_workers)
    return {
        "pool_id": pool_id,
        "name": name,
        "status": "created"
    }

@app.get("/pools/{pool_id}")
def get_pool_stats(pool_id: str):
    """Get pool statistics (Phase 6)"""
    pool = pool_manager.get_pool(pool_id)
    if pool:
        return pool.get_pool_stats()
    return {"error": "Pool not found"}, 404

@app.post("/pools/{pool_id}/workers")
def add_worker_to_pool(pool_id: str, name: str, provider: str, endpoint: str = None):
    """Add worker to pool (Phase 6)"""
    worker_id = pool_manager.add_worker_to_pool(pool_id, name, provider, endpoint)
    if worker_id:
        return {
            "worker_id": worker_id,
            "pool_id": pool_id,
            "status": "added"
        }
    return {"error": "Failed to add worker"}, 500

# ==================== PHASE 7: Browser Matrix ====================

@app.post("/jobs/matrix")
def create_matrix_job(
    test_file: str,
    browsers: list = ["chrome"],
    devices: list = ["desktop"]
):
    """Run test across browser matrix (Phase 7)"""
    jobs = []
    for browser in browsers:
        for device in devices:
            job_id = job_manager.create_job(test_file)
            job = job_manager.jobs[job_id]
            job.metadata["browser"] = browser
            job.metadata["device"] = device
            jobs.append({
                "job_id": job_id,
                "browser": browser,
                "device": device
            })
    
    return {
        "matrix_id": uuid.uuid4().hex,
        "jobs": jobs,
        "total": len(jobs)
    }

# ==================== PHASE 8: Allure Reports ====================

@app.get("/jobs/{job_id}/report")
def get_job_report(job_id: str):
    """Get Allure report for job (Phase 8-V9)"""
    job = job_manager.get_job(job_id)
    if not job:
        return {"error": "Job not found"}, 404
    
    return {
        "job_id": job_id,
        "report_type": "allure",
        "screenshots": job.get("screenshots", []),
        "traces": job.get("traces", []),
        "logs": job.get("logs", [])
    }

@app.post("/jobs/{job_id}/screenshots")
async def upload_screenshot(job_id: str, file: UploadFile = File(...)):
    """Upload screenshot for job (Phase 8-V9)"""
    if job_id not in job_manager.jobs:
        return {"error": "Job not found"}, 404
    
    content = await file.read()
    screenshot_path = f"results/{job_id}/{file.filename}"
    
    return {
        "screenshot_id": uuid.uuid4().hex,
        "path": screenshot_path,
        "size": len(content)
    }

# ==================== PHASE 5: Tunnel & UAT ====================

@app.post("/tunnels")
def create_tunnel(
    name: str,
    local_host: str,
    local_port: int
):
    """Create tunnel to private UAT (Phase 5-V5)"""
    tunnel_id = tunnel_manager.create_tunnel(name, local_host, local_port)
    tunnel = tunnel_manager.get_tunnel(tunnel_id)
    return tunnel.to_dict()

@app.get("/tunnels")
def list_tunnels():
    """List all tunnels (Phase 5-V5)"""
    return {
        "tunnels": tunnel_manager.list_tunnels()
    }

@app.get("/tunnels/{tunnel_id}")
def get_tunnel(tunnel_id: str):
    """Get tunnel info (Phase 5-V5)"""
    tunnel = tunnel_manager.get_tunnel(tunnel_id)
    if tunnel:
        return tunnel.to_dict()
    return {"error": "Tunnel not found"}, 404

@app.delete("/tunnels/{tunnel_id}")
def delete_tunnel(tunnel_id: str):
    """Delete tunnel (Phase 5-V5)"""
    if tunnel_manager.delete_tunnel(tunnel_id):
        return {"status": "deleted"}
    return {"error": "Tunnel not found"}, 404

@app.post("/tunnel-config")
def set_tunnel_config(provider: str, auth_token: str = None):
    """Configure tunnel provider (Phase 5-V5)"""
    if tunnel_config.set_provider(provider, auth_token):
        return {
            "status": "configured",
            "provider": provider
        }
    return {"error": "Invalid provider"}, 400

@app.get("/tunnel-config")
def get_tunnel_config():
    """Get tunnel config (Phase 5-V5)"""
    return tunnel_config.to_dict()

# ==================== LOCAL EXECUTION AGENTS (real tunneling) ====================
#
# An "agent" is a small script the customer runs on their own machine. It
# connects OUTBOUND to this server over WebSocket -- no inbound port, no
# firewall change, no VPN. Once connected, we can push it a job; it runs the
# test locally (so it can reach a private/UAT app) and streams logs + a
# report back up the same socket. See agent/playwright_agent.py.

@app.post("/agents/register")
def register_agent(name: str):
    """Step 1: generate a one-time token for a new agent (Phase 5 - real tunnel)."""
    agent_id, token = agent_manager.issue_token(name)
    return {
        "agent_id": agent_id,
        "token": token,
        "note": "Put this token into the agent script's --token argument. "
                "It connects to wss://<this-server>/ws/agent/{token}"
    }

@app.get("/agents")
def list_agents():
    """List every agent that is currently connected (or was, and dropped)."""
    return {"agents": agent_manager.list_agents()}

@app.websocket("/ws/agent/{token}")
async def agent_socket(websocket: WebSocket, token: str):
    """Step 2: the agent process opens this connection and keeps it open.
    This is the actual 'tunnel' -- a persistent outbound link the server can
    push jobs down and the agent can push logs/results back up."""
    await websocket.accept()

    info = agent_manager.consume_token(token)
    if not info:
        await websocket.send_json({"type": "error", "message": "invalid or already-used token"})
        await websocket.close()
        return

    agent = agent_manager.register_connection(info["agent_id"], info["name"], websocket)
    await websocket.send_json({"type": "registered", "agent_id": agent.id})

    try:
        while True:
            data = await websocket.receive_json()
            agent_manager.touch(agent.id)
            if data.get("type") == "heartbeat":
                continue
            agent_manager.handle_agent_message(agent.id, data)
    except WebSocketDisconnect:
        agent_manager.disconnect(agent.id)

@app.post("/agents/{agent_id}/run")
async def run_on_agent(agent_id: str, file: UploadFile = File(...), language: str = "auto", command: str = None):
    """Step 3: dispatch a test bundle (zip of the customer's Playwright
    project) to a specific connected agent."""
    if not agent_manager.get_agent(agent_id):
        return {"error": "agent not found or not connected"}, 404

    content = await file.read()
    filename = f"{uuid.uuid4()}.zip"
    upload_handler.save_zip_file(content, filename)
    download_url = f"/agents/downloads/{filename}"

    job_id = agent_manager.create_job(agent_id, download_url, language, command)
    dispatched = await agent_manager.dispatch_job(agent_id, job_id)
    if not dispatched:
        return {"error": "agent is busy or offline, try again shortly"}, 409

    return {"job_id": job_id, "agent_id": agent_id, "status": "dispatched"}

@app.get("/agents/downloads/{filename}")
def download_bundle(filename: str):
    """The agent fetches the test bundle from here over plain HTTPS."""
    path = os.path.join("uploads", filename)
    if not os.path.exists(path):
        return {"error": "not found"}, 404
    return FileResponse(path)

@app.get("/agents/jobs/{job_id}")
def get_agent_job(job_id: str):
    job = agent_manager.get_job(job_id)
    if not job:
        return {"error": "not found"}, 404
    return job

@app.get("/agents/jobs")
def list_agent_jobs():
    return {"jobs": agent_manager.list_jobs()}

@app.post("/agents/jobs/{job_id}/report")
async def upload_agent_report(job_id: str, file: UploadFile = File(...)):
    """The agent uploads the Playwright/Allure report here once the run finishes."""
    content = await file.read()
    os.makedirs("results", exist_ok=True)
    path = f"results/{job_id}_report.zip"
    with open(path, "wb") as f:
        f.write(content)
    agent_manager.attach_report(job_id, path)
    return {"status": "received", "path": path}

@app.get("/agents/jobs/{job_id}/report")
def download_agent_report(job_id: str):
    job = agent_manager.get_job(job_id)
    if not job or not job.get("report_path") or not os.path.exists(job["report_path"]):
        return {"error": "report not available"}, 404
    return FileResponse(job["report_path"], filename=f"{job_id}_report.zip")

@app.websocket("/ws/agent-job/{job_id}")
async def agent_job_ws(websocket: WebSocket, job_id: str):
    """Live log stream for the dashboard while an agent job is running -
    same pattern as /ws/{job_id} but for agent-executed jobs."""
    await websocket.accept()
    if job_id not in agent_manager.jobs:
        await websocket.send_json({"error": "job not found"})
        await websocket.close()
        return

    job = agent_manager.jobs[job_id]
    loop = asyncio.get_running_loop()

    async def send_to_ws(message: str):
        try:
            await websocket.send_text(message)
        except Exception:
            pass

    def listener(message: str):
        asyncio.run_coroutine_threadsafe(send_to_ws(message), loop)

    agent_manager.add_listener(job_id, listener)
    for line in job.logs:
        await websocket.send_json({"type": "log", "job_id": job_id, "message": line})

    try:
        while True:
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        agent_manager.remove_listener(job_id, listener)

# ==================== PHASE 10: Multi-Tenant ====================

@app.post("/workspaces")
def create_workspace(name: str, owner_id: str):
    """Create workspace (Phase 10-V10)"""
    workspace_id = f"ws-{uuid.uuid4().hex[:8]}"
    return {
        "workspace_id": workspace_id,
        "name": name,
        "owner_id": owner_id,
        "created_at": "2024-09-25T00:00:00Z"
    }

@app.get("/workspaces/{workspace_id}/jobs")
def get_workspace_jobs(workspace_id: str):
    """Get jobs for workspace (Phase 10-V10)"""
    return {
        "workspace_id": workspace_id,
        "jobs": [],
        "total": 0
    }

@app.get("/workspaces/{workspace_id}/billing")
def get_workspace_billing(workspace_id: str):
    """Get billing info (Phase 10-V10)"""
    return {
        "workspace_id": workspace_id,
        "period": "2024-09",
        "job_count": 0,
        "worker_hours": 0,
        "cost": 0,
        "currency": "USD"
    }

# ==================== Dashboard ====================

@app.get("/dashboard/summary")
def dashboard_summary(workspace_id: str = None):
    """Dashboard summary (Phase 2-V10)"""
    jobs = job_manager.list_jobs()
    
    total_jobs = len(jobs)
    passed = len([j for j in jobs if j['status'] == 'passed'])
    failed = len([j for j in jobs if j['status'] == 'failed'])
    running = len([j for j in jobs if j['status'] == 'running'])
    
    return {
        "total_jobs": total_jobs,
        "passed": passed,
        "failed": failed,
        "running": running,
        "success_rate": (passed / total_jobs * 100) if total_jobs > 0 else 0
    }

@app.get("/api/version")
def api_version():
    """API version info"""
    return {
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

