import threading
import uuid
from typing import Dict, List


class Worker:
    def __init__(self, worker_id: str, name: str, provider: str, endpoint: str = None):
        self.id = worker_id
        self.name = name
        self.provider = provider  # local, docker, railway, aws, gcp
        self.endpoint = endpoint or f"http://localhost:8000"
        self.status = "online"
        self.current_jobs = 0
        self.max_jobs = 3
        self.cpu_cores = 2
        self.memory_gb = 4
        self.total_completed = 0
        self.success_count = 0

    def is_available(self) -> bool:
        return self.status == "online" and self.current_jobs < self.max_jobs

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "provider": self.provider,
            "endpoint": self.endpoint,
            "status": self.status,
            "current_jobs": self.current_jobs,
            "max_jobs": self.max_jobs,
            "cpu_cores": self.cpu_cores,
            "memory_gb": self.memory_gb,
            "success_rate": (self.success_count / self.total_completed * 100) if self.total_completed > 0 else 0
        }


class WorkerPool:
    def __init__(self, pool_id: str, name: str, min_workers: int = 1, max_workers: int = 5):
        self.id = pool_id
        self.name = name
        self.min_workers = min_workers
        self.max_workers = max_workers
        self.workers: Dict[str, Worker] = {}
        self.lock = threading.Lock()
        self.auto_scale = True
        self._initialize_default_workers()

    def _initialize_default_workers(self):
        """Create default local workers"""
        worker = Worker(
            worker_id="worker-local-1",
            name="Local Worker",
            provider="local",
            endpoint="http://127.0.0.1:8000"
        )
        self.workers[worker.id] = worker

    def add_worker(self, name: str, provider: str, endpoint: str = None) -> str:
        with self.lock:
            worker_id = f"worker-{uuid.uuid4().hex[:8]}"
            worker = Worker(worker_id, name, provider, endpoint)
            self.workers[worker_id] = worker
            return worker_id

    def remove_worker(self, worker_id: str) -> bool:
        with self.lock:
            if worker_id in self.workers and self.workers[worker_id].current_jobs == 0:
                del self.workers[worker_id]
                return True
        return False

    def get_available_worker(self) -> Worker:
        """Get least busy available worker"""
        with self.lock:
            available = [w for w in self.workers.values() if w.is_available()]
            if not available:
                return None
            return min(available, key=lambda w: w.current_jobs)

    def assign_job(self, worker_id: str) -> bool:
        with self.lock:
            if worker_id in self.workers:
                self.workers[worker_id].current_jobs += 1
                return True
        return False

    def release_job(self, worker_id: str, success: bool = True) -> bool:
        with self.lock:
            if worker_id in self.workers:
                worker = self.workers[worker_id]
                worker.current_jobs = max(0, worker.current_jobs - 1)
                worker.total_completed += 1
                if success:
                    worker.success_count += 1
                return True
        return False

    def list_workers(self) -> List[dict]:
        with self.lock:
            return [w.to_dict() for w in self.workers.values()]

    def get_pool_stats(self) -> dict:
        with self.lock:
            total_workers = len(self.workers)
            online_workers = len([w for w in self.workers.values() if w.status == "online"])
            total_capacity = sum(w.max_jobs for w in self.workers.values())
            used_capacity = sum(w.current_jobs for w in self.workers.values())
            
            return {
                "pool_id": self.id,
                "pool_name": self.name,
                "total_workers": total_workers,
                "online_workers": online_workers,
                "total_capacity": total_capacity,
                "used_capacity": used_capacity,
                "available_slots": total_capacity - used_capacity,
                "utilization": (used_capacity / total_capacity * 100) if total_capacity > 0 else 0
            }


class PoolManager:
    def __init__(self):
        self.pools: Dict[str, WorkerPool] = {}
        self.lock = threading.Lock()
        self._create_default_pool()

    def _create_default_pool(self):
        """Create default worker pool"""
        pool_id = "pool-default"
        pool = WorkerPool(pool_id, "Default Pool")
        self.pools[pool_id] = pool

    def create_pool(self, name: str, min_workers: int = 1, max_workers: int = 5) -> str:
        with self.lock:
            pool_id = f"pool-{uuid.uuid4().hex[:8]}"
            pool = WorkerPool(pool_id, name, min_workers, max_workers)
            self.pools[pool_id] = pool
            return pool_id

    def get_pool(self, pool_id: str) -> WorkerPool:
        return self.pools.get(pool_id)

    def list_pools(self) -> List[dict]:
        with self.lock:
            return [p.get_pool_stats() for p in self.pools.values()]

    def add_worker_to_pool(self, pool_id: str, name: str, provider: str, endpoint: str = None) -> str:
        pool = self.get_pool(pool_id)
        if pool:
            return pool.add_worker(name, provider, endpoint)
        return None

    def get_next_worker(self, pool_id: str = "pool-default") -> Worker:
        """Get next available worker from pool"""
        pool = self.get_pool(pool_id)
        if pool:
            return pool.get_available_worker()
        return None


# Global instance
pool_manager = PoolManager()
