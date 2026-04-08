from typing import Dict, Optional
from models.schemas import ExtractionStatus
import threading

_jobs: Dict[str, ExtractionStatus] = {}
_lock = threading.Lock()


def create_job(job_id: str, status: ExtractionStatus):
    with _lock:
        _jobs[job_id] = status


def get_job(job_id: str) -> Optional[ExtractionStatus]:
    with _lock:
        return _jobs.get(job_id)


def update_job(job_id: str, **kwargs):
    with _lock:
        if job_id in _jobs:
            for k, v in kwargs.items():
                setattr(_jobs[job_id], k, v)


def list_jobs():
    with _lock:
        return list(_jobs.values())


def delete_job(job_id: str):
    with _lock:
        _jobs.pop(job_id, None)
