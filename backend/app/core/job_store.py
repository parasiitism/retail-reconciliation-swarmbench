from datetime import datetime, timezone
from uuid import uuid4

from backend.app.core.models import ReconciliationJob


JOBS: dict[str, ReconciliationJob] = {}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_job() -> ReconciliationJob:
    job = ReconciliationJob(
        job_id=str(uuid4()),
        status="pending",
        created_at=utc_now(),
    )

    JOBS[job.job_id] = job
    return job


def update_job(job_id: str, **changes) -> ReconciliationJob:
    job = JOBS[job_id]

    updated_data = job.model_dump() if hasattr(job, "model_dump") else job.dict()
    updated_data.update(changes)

    updated_job = ReconciliationJob(**updated_data)
    JOBS[job_id] = updated_job

    return updated_job


def get_job(job_id: str) -> ReconciliationJob | None:
    return JOBS.get(job_id)
