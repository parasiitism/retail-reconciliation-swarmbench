from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select

from backend.app.core.database import SessionLocal, init_database
from backend.app.core.db_models import JobRecord
from backend.app.core.models import ReconciliationJob


def init_job_store() -> None:
    init_database()


def job_record_to_model(record: JobRecord) -> ReconciliationJob:
    return ReconciliationJob(
        job_id=record.job_id,
        status=record.status,
        report_path=record.report_path,
        error_message=record.error_message,
        created_at=record.created_at,
        completed_at=record.completed_at,
    )


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_job() -> ReconciliationJob:
    init_job_store()

    job = ReconciliationJob(
        job_id=str(uuid4()),
        status="pending",
        created_at=utc_now(),
    )

    record = JobRecord(
        job_id=job.job_id,
        status=job.status,
        report_path=job.report_path,
        error_message=job.error_message,
        created_at=job.created_at,
        completed_at=job.completed_at,
    )

    with SessionLocal() as session:
        session.add(record)
        session.commit()

    return job


def update_job(job_id: str, **changes) -> ReconciliationJob:
    init_job_store()

    with SessionLocal() as session:
        record = session.get(JobRecord, job_id)

        if record is None:
            raise KeyError(f"Job not found: {job_id}")

        current_job = job_record_to_model(record)
        updated_data = (
            current_job.model_dump()
            if hasattr(current_job, "model_dump")
            else current_job.dict()
        )
        updated_data.update(changes)

        updated_job = ReconciliationJob(**updated_data)

        record.status = updated_job.status
        record.report_path = updated_job.report_path
        record.error_message = updated_job.error_message
        record.created_at = updated_job.created_at
        record.completed_at = updated_job.completed_at
        session.commit()

        return updated_job


def get_job(job_id: str) -> ReconciliationJob | None:
    init_job_store()

    with SessionLocal() as session:
        record = session.get(JobRecord, job_id)

        if record is None:
            return None

        return job_record_to_model(record)


def list_jobs() -> list[ReconciliationJob]:
    init_job_store()

    statement = select(JobRecord).order_by(JobRecord.created_at.desc())

    with SessionLocal() as session:
        records = session.scalars(statement).all()

    return [job_record_to_model(record) for record in records]
