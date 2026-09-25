"""
Agent Manager
=============
Handles LOCAL EXECUTION AGENTS: lightweight processes that customers run on
their own machine (inside their own network). An agent makes an OUTBOUND
WebSocket connection to this server -- so nothing needs to be opened/forwarded
on the customer's firewall or router. Once connected, the server can push it
a job; the agent runs the test locally (where it can reach a private/UAT app)
and streams logs + a final report back up the same connection.

This replaces the old tunnel_manager.py simulation with something that
actually works end to end.
"""
import json
import secrets
from datetime import datetime
from typing import Callable, Dict, List, Optional

from fastapi import WebSocket


class ConnectedAgent:
    def __init__(self, agent_id: str, name: str, websocket: WebSocket):
        self.id = agent_id
        self.name = name
        self.websocket = websocket
        self.status = "idle"  # idle | busy | offline
        self.current_job_id: Optional[str] = None
        self.connected_at = datetime.utcnow()
        self.last_seen = datetime.utcnow()

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "status": self.status,
            "current_job_id": self.current_job_id,
            "connected_at": self.connected_at.isoformat(),
            "last_seen": self.last_seen.isoformat(),
        }


class AgentJob:
    """A job can come from three sources:
    - upload: a zip the customer uploaded through the dashboard (download_url set)
    - git: a repo URL the agent clones itself (git_url set) - your code stays
      in the customer's own git host, never touches our server or storage
    - local: nothing is sent at all - the agent runs whatever is already on
      disk on the customer's machine (source == "local"). Nobody's code
      leaves their machine in this mode.
    """
    def __init__(self, job_id: str, agent_id: str, language: str, command: Optional[str],
                 download_url: Optional[str] = None, git_url: Optional[str] = None,
                 git_ref: Optional[str] = None, source: str = "upload"):
        self.id = job_id
        self.agent_id = agent_id
        self.download_url = download_url
        self.git_url = git_url
        self.git_ref = git_ref
        self.source = source
        self.language = language
        self.command = command
        self.status = "dispatched"  # dispatched | running | passed | failed
        self.logs: List[str] = []
        self.exit_code: Optional[int] = None
        self.report_path: Optional[str] = None
        self.created_at = datetime.utcnow()
        self.completed_at = None
        self.listeners: List[Callable] = []

    def to_dict(self):
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "status": self.status,
            "logs": self.logs,
            "exit_code": self.exit_code,
            "report_path": self.report_path,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


class AgentManager:
    def __init__(self):
        self.agents: Dict[str, ConnectedAgent] = {}
        # token -> {"agent_id":..., "name":...}; consumed once the agent connects
        self.pending_tokens: Dict[str, dict] = {}
        self.jobs: Dict[str, AgentJob] = {}

    # ---------- registration / connection ----------

    def issue_token(self, name: str) -> tuple[str, str]:
        """Called from the REST API before the agent ever connects.
        Returns (agent_id, token). The customer puts the token into the
        agent script's config; the token is single-use to open the socket."""
        agent_id = f"agent-{secrets.token_hex(4)}"
        token = secrets.token_urlsafe(24)
        self.pending_tokens[token] = {"agent_id": agent_id, "name": name}
        return agent_id, token

    def consume_token(self, token: str) -> Optional[dict]:
        return self.pending_tokens.pop(token, None)

    def register_connection(self, agent_id: str, name: str, websocket: WebSocket) -> ConnectedAgent:
        agent = ConnectedAgent(agent_id, name, websocket)
        self.agents[agent_id] = agent
        return agent

    def disconnect(self, agent_id: str):
        if agent_id in self.agents:
            self.agents[agent_id].status = "offline"

    def touch(self, agent_id: str):
        if agent_id in self.agents:
            self.agents[agent_id].last_seen = datetime.utcnow()

    def list_agents(self) -> list:
        return [a.to_dict() for a in self.agents.values()]

    def get_agent(self, agent_id: str) -> Optional[ConnectedAgent]:
        return self.agents.get(agent_id)

    # ---------- job dispatch ----------

    def create_job(self, agent_id: str, language: str, command: Optional[str],
                    download_url: Optional[str] = None, git_url: Optional[str] = None,
                    git_ref: Optional[str] = None, source: str = "upload") -> str:
        job_id = f"job-{secrets.token_hex(4)}"
        self.jobs[job_id] = AgentJob(job_id, agent_id, language, command,
                                      download_url=download_url, git_url=git_url,
                                      git_ref=git_ref, source=source)
        return job_id

    async def dispatch_job(self, agent_id: str, job_id: str) -> bool:
        agent = self.agents.get(agent_id)
        job = self.jobs.get(job_id)
        if not agent or not job:
            return False
        if agent.status != "idle":
            return False
        agent.status = "busy"
        agent.current_job_id = job_id
        payload = {
            "type": "job",
            "job_id": job.id,
            "source": job.source,
            "language": job.language,
            "command": job.command,
        }
        if job.download_url:
            payload["download_url"] = job.download_url
        if job.git_url:
            payload["git_url"] = job.git_url
            payload["git_ref"] = job.git_ref
        await agent.websocket.send_json(payload)
        return True

    # ---------- messages coming back from the agent ----------

    def handle_agent_message(self, agent_id: str, message: dict):
        job_id = message.get("job_id")
        job = self.jobs.get(job_id)
        if not job:
            return
        mtype = message.get("type")

        if mtype == "log":
            job.status = "running"
            line = message.get("message", "")
            job.logs.append(line)
            self._broadcast(job, {"type": "log", "job_id": job_id, "message": line})

        elif mtype == "result":
            job.status = message.get("status", "failed")
            job.exit_code = message.get("exit_code")
            job.completed_at = datetime.utcnow()
            self._broadcast(job, {
                "type": job.status,
                "job_id": job_id,
                "exit_code": job.exit_code,
            })
            agent = self.agents.get(agent_id)
            if agent:
                agent.status = "idle"
                agent.current_job_id = None

    def attach_report(self, job_id: str, path: str):
        if job_id in self.jobs:
            self.jobs[job_id].report_path = path

    def _broadcast(self, job: AgentJob, event: dict):
        for listener in job.listeners:
            try:
                listener(json.dumps(event))
            except Exception:
                pass

    def add_listener(self, job_id: str, listener: Callable):
        if job_id in self.jobs:
            self.jobs[job_id].listeners.append(listener)

    def remove_listener(self, job_id: str, listener: Callable):
        if job_id in self.jobs and listener in self.jobs[job_id].listeners:
            self.jobs[job_id].listeners.remove(listener)

    def get_job(self, job_id: str) -> Optional[dict]:
        job = self.jobs.get(job_id)
        return job.to_dict() if job else None

    def list_jobs(self) -> list:
        return [j.to_dict() for j in self.jobs.values()]


# Global instance
agent_manager = AgentManager()
