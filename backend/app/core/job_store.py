import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from backend.app.core.models import ReconciliationJob


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "reconciliation.db"


def get_connection() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_job_store() -> None:
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS jobs (
                job_id TEXT PRIMARY KEY,
                status TEXT NOT NULL,
                report_path TEXT,
                error_message TEXT,
                created_at TEXT NOT NULL,
                completed_at TEXT
            )
            """
        )


def row_to_job(row: sqlite3.Row) -> ReconciliationJob:
    return ReconciliationJob(
        job_id=row["job_id"],
        status=row["status"],
        report_path=row["report_path"],
        error_message=row["error_message"],
        created_at=row["created_at"],
        completed_at=row["completed_at"],
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

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO jobs (
                job_id, status, report_path, error_message, created_at, completed_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                job.job_id,
                job.status,
                job.report_path,
                job.error_message,
                job.created_at,
                job.completed_at,
            ),
        )

    return job


def update_job(job_id: str, **changes) -> ReconciliationJob:
    init_job_store()

    current_job = get_job(job_id)

    if current_job is None:
        raise KeyError(f"Job not found: {job_id}")

    updated_data = (
        current_job.model_dump()
        if hasattr(current_job, "model_dump")
        else current_job.dict()
    )
    updated_data.update(changes)

    updated_job = ReconciliationJob(**updated_data)

    with get_connection() as connection:
        connection.execute(
            """
            UPDATE jobs
            SET status = ?,
                report_path = ?,
                error_message = ?,
                created_at = ?,
                completed_at = ?
            WHERE job_id = ?
            """,
            (
                updated_job.status,
                updated_job.report_path,
                updated_job.error_message,
                updated_job.created_at,
                updated_job.completed_at,
                updated_job.job_id,
            ),
        )

    return updated_job


def get_job(job_id: str) -> ReconciliationJob | None:
    init_job_store()

    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT job_id, status, report_path, error_message, created_at, completed_at
            FROM jobs
            WHERE job_id = ?
            """,
            (job_id,),
        ).fetchone()

    if row is None:
        return None

    return row_to_job(row)


def list_jobs() -> list[ReconciliationJob]:
    init_job_store()

    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT job_id, status, report_path, error_message, created_at, completed_at
            FROM jobs
            ORDER BY created_at DESC
            """
        ).fetchall()

    return [row_to_job(row) for row in rows]
