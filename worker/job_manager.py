import uuid
import threading
import subprocess
import json
from datetime import datetime
from typing import Dict, List, Callable
from enum import Enum


class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Job:
    def __init__(self, job_id: str, test_file: str, user_id: str = None):
        self.id = job_id
        self.test_file = test_file
        self.user_id = user_id
        self.status = JobStatus.QUEUED
        self.logs = []
        self.screenshots = []
        self.traces = []
        self.created_at = datetime.utcnow()
        self.started_at = None
        self.completed_at = None
        self.exit_code = None
        self.listeners: List[Callable] = []
        self.process = None
        self.metadata = {}


class JobManager:
    def __init__(self):
        self.jobs: Dict[str, Job] = {}
        self.lock = threading.Lock()
        self.worker_pool = []
        self.max_workers = 3

    def create_job(self, test_file: str, user_id: str = None) -> str:
        job_id = str(uuid.uuid4())
        job = Job(job_id, test_file, user_id)
        with self.lock:
            self.jobs[job_id] = job
        self._start_job_thread(job_id)
        return job_id

    def _start_job_thread(self, job_id: str):
        thread = threading.Thread(
            target=self._run_job,
            args=(job_id,),
            daemon=True
        )
        thread.start()

    def _run_job(self, job_id: str):
        job = self.jobs[job_id]
        job.status = JobStatus.RUNNING
        job.started_at = datetime.utcnow()
        self._broadcast_event(job_id, {
            "type": "job_started",
            "job_id": job_id,
            "timestamp": job.started_at.isoformat()
        })

        try:
            job.process = subprocess.Popen(
                ["pytest", f"tests/{job.test_file}", "-v", "-s", "--tb=short"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )

            for line in job.process.stdout:
                line = line.strip()
                if line:
                    job.logs.append(line)
                    self._broadcast_event(job_id, {
                        "type": "log",
                        "message": line,
                        "timestamp": datetime.utcnow().isoformat()
                    })

            job.process.wait()
            job.exit_code = job.process.returncode

            if job.exit_code == 0:
                job.status = JobStatus.PASSED
                event_type = "job_passed"
            else:
                job.status = JobStatus.FAILED
                event_type = "job_failed"

            job.completed_at = datetime.utcnow()

            self._broadcast_event(job_id, {
                "type": event_type,
                "job_id": job_id,
                "exit_code": job.exit_code,
                "duration": (job.completed_at - job.started_at).total_seconds(),
                "timestamp": job.completed_at.isoformat()
            })

        except Exception as e:
            job.status = JobStatus.FAILED
            job.logs.append(f"ERROR: {str(e)}")
            self._broadcast_event(job_id, {
                "type": "job_failed",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            })

    def _broadcast_event(self, job_id: str, event: dict):
        if job_id in self.jobs:
            job = self.jobs[job_id]
            for listener in job.listeners:
                try:
                    listener(json.dumps(event))
                except Exception:
                    pass

    def add_listener(self, job_id: str, listener: Callable):
        if job_id in self.jobs:
            self.jobs[job_id].listeners.append(listener)

    def remove_listener(self, job_id: str, listener: Callable):
        if job_id in self.jobs:
            if listener in self.jobs[job_id].listeners:
                self.jobs[job_id].listeners.remove(listener)

    def get_job(self, job_id: str) -> dict:
        if job_id not in self.jobs:
            return None
        job = self.jobs[job_id]
        return {
            "id": job.id,
            "status": job.status.value,
            "logs": job.logs,
            "screenshots": job.screenshots,
            "traces": job.traces,
            "exit_code": job.exit_code,
            "created_at": job.created_at.isoformat(),
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            "user_id": job.user_id
        }

    def list_jobs(self, user_id: str = None) -> List[dict]:
        jobs = []
        for job_id, job in self.jobs.items():
            if user_id and job.user_id != user_id:
                continue
            jobs.append(self.get_job(job_id))
        return sorted(jobs, key=lambda x: x['created_at'], reverse=True)

    def cancel_job(self, job_id: str) -> bool:
        if job_id in self.jobs:
            job = self.jobs[job_id]
            if job.process:
                job.process.terminate()
                job.status = JobStatus.CANCELLED
                return True
        return False


# Global instance
job_manager = JobManager()
