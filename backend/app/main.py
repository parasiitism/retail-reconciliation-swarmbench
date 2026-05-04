import json
from pathlib import Path
from typing import Annotated
from uuid import uuid4

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.openapi.utils import get_openapi

from backend.app.core.catalog import load_product_catalog
from backend.app.core.config import PRODUCT_CATALOG_PATH, REPORTS_DIR, SAMPLE_RETAIL_DIR, UPLOADS_DIR
from backend.app.core.csv_profiler import profile_csv
from backend.app.core.dashboard import build_dashboard_summary
from backend.app.core.job_store import create_job, get_job, list_jobs, update_job, utc_now
from backend.app.core.reconciliation import reconcile_many_csvs
from backend.app.core.report_writer import write_json_report
from backend.app.core.validation import validate_report

app = FastAPI(
    title="Multi-Agent Reconciliation Platform",
    version="0.1.0",
)


def model_to_dict(model) -> dict:
    if hasattr(model, "model_dump_json"):
        return json.loads(model.model_dump_json())
    return json.loads(model.json())


def custom_openapi() -> dict:
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        routes=app.routes,
    )

    upload_schema = openapi_schema["components"]["schemas"].get(
        "Body_upload_csv_job_jobs_upload_csv_post"
    )
    if upload_schema:
        upload_schema["properties"]["files"]["items"] = {
            "type": "string",
            "format": "binary",
        }

    app.openapi_schema = openapi_schema
    return app.openapi_schema


def source_id_from_filename(filename: str, index: int) -> str:
    source_id = Path(filename).stem.strip().lower()
    source_id = source_id.replace(" ", "_").replace("-", "_")

    return source_id or f"source_{index}"


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/dashboard/summary")
def get_dashboard_summary() -> dict:
    return build_dashboard_summary()


@app.post("/jobs/run-demo")
def run_demo_job() -> dict:
    product_catalog = load_product_catalog(PRODUCT_CATALOG_PATH)

    source_paths = {
        "atlanta": SAMPLE_RETAIL_DIR / "atlanta.csv",
        "boston": SAMPLE_RETAIL_DIR / "boston.csv",
    }

    report = reconcile_many_csvs(
        source_paths=source_paths,
        product_catalog=product_catalog,
    )
    validation_result = validate_report(report)

    output_path = REPORTS_DIR / "latest_report.json"
    saved_path = write_json_report(report, output_path)

    return {
        "status": "completed",
        "report_path": str(saved_path),
        "validation": model_to_dict(validation_result),
        "report": model_to_dict(report),
    }


@app.post("/jobs/demo")
def create_demo_job() -> dict:
    job = create_job()
    job = update_job(job.job_id, status="running")

    try:
        product_catalog = load_product_catalog(PRODUCT_CATALOG_PATH)

        source_paths = {
            "atlanta": SAMPLE_RETAIL_DIR / "atlanta.csv",
            "boston": SAMPLE_RETAIL_DIR / "boston.csv",
        }

        report = reconcile_many_csvs(
            source_paths=source_paths,
            product_catalog=product_catalog,
        )
        validation_result = validate_report(report)

        output_path = REPORTS_DIR / f"{job.job_id}_report.json"
        saved_path = write_json_report(report, output_path)

        job = update_job(
            job.job_id,
            status="completed",
            report_path=str(saved_path),
            completed_at=utc_now(),
        )

        return {
            "job": model_to_dict(job),
            "validation": model_to_dict(validation_result),
        }

    except Exception as exc:
        job = update_job(
            job.job_id,
            status="failed",
            error_message=str(exc),
            completed_at=utc_now(),
        )

        return {
            "job": model_to_dict(job),
        }


@app.post("/jobs/upload-csv")
async def upload_csv_job(
    files: Annotated[
        list[UploadFile],
        File(description="One or more CSV files to reconcile"),
    ],
) -> dict:
    if not files:
        raise HTTPException(status_code=400, detail="At least one CSV file is required")

    job = create_job()
    job = update_job(job.job_id, status="running")

    try:
        upload_dir = UPLOADS_DIR / job.job_id
        upload_dir.mkdir(parents=True, exist_ok=True)

        source_paths: dict[str, Path] = {}

        for index, uploaded_file in enumerate(files, start=1):
            original_filename = uploaded_file.filename or f"source_{index}.csv"

            if not original_filename.lower().endswith(".csv"):
                raise HTTPException(
                    status_code=400,
                    detail=f"Only CSV files are supported right now: {original_filename}",
                )

            safe_filename = Path(original_filename).name
            saved_path = upload_dir / safe_filename

            file_bytes = await uploaded_file.read()
            saved_path.write_bytes(file_bytes)

            source_id = source_id_from_filename(safe_filename, index)

            if source_id in source_paths:
                source_id = f"{source_id}_{index}"

            source_paths[source_id] = saved_path

        product_catalog = load_product_catalog(PRODUCT_CATALOG_PATH)

        report = reconcile_many_csvs(
            source_paths=source_paths,
            product_catalog=product_catalog,
        )

        validation_result = validate_report(report)

        output_path = REPORTS_DIR / f"{job.job_id}_report.json"
        saved_report_path = write_json_report(report, output_path)

        job = update_job(
            job.job_id,
            status="completed",
            report_path=str(saved_report_path),
            completed_at=utc_now(),
        )

        return {
            "job": model_to_dict(job),
            "validation": model_to_dict(validation_result),
            "uploaded_sources": list(source_paths.keys()),
        }

    except HTTPException as exc:
        job = update_job(
            job.job_id,
            status="failed",
            error_message=str(exc.detail),
            completed_at=utc_now(),
        )

        raise exc

    except Exception as exc:
        job = update_job(
            job.job_id,
            status="failed",
            error_message=str(exc),
            completed_at=utc_now(),
        )

        return {
            "job": model_to_dict(job),
        }


@app.get("/jobs")
def get_jobs() -> dict:
    return {
        "jobs": [model_to_dict(job) for job in list_jobs()]
    }


@app.get("/jobs/{job_id}")
def get_job_status(job_id: str) -> dict:
    job = get_job(job_id)

    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    return {
        "job": model_to_dict(job),
    }


@app.get("/jobs/{job_id}/report")
def get_job_report(job_id: str) -> dict:
    job = get_job(job_id)

    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status != "completed" or job.report_path is None:
        raise HTTPException(status_code=400, detail="Report is not available")

    report_path = Path(job.report_path)

    if not report_path.exists():
        raise HTTPException(status_code=404, detail="Report file not found")

    return {
        "job": model_to_dict(job),
        "report": json.loads(report_path.read_text(encoding="utf-8")),
    }


@app.get("/reports/latest")
def get_latest_report() -> dict:
    report_path = REPORTS_DIR / "latest_report.json"

    if not report_path.exists():
        return {
            "status": "not_found",
            "message": "No report has been generated yet.",
        }

    return {
        "status": "found",
        "report_path": str(report_path),
        "report": json.loads(report_path.read_text(encoding="utf-8")),
    }


@app.post("/schema/profile-csv")
async def profile_csv_schema(
    file: Annotated[
        UploadFile,
        File(description="CSV file to inspect before reconciliation"),
    ],
) -> dict:
    original_filename = file.filename or "uploaded.csv"

    if not original_filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail=f"Only CSV files are supported right now: {original_filename}",
        )

    profile_dir = UPLOADS_DIR / "_schema_profiles"
    profile_dir.mkdir(parents=True, exist_ok=True)

    safe_filename = Path(original_filename).name
    saved_path = profile_dir / f"{uuid4()}_{safe_filename}"

    file_bytes = await file.read()
    saved_path.write_bytes(file_bytes)

    return profile_csv(saved_path)


app.openapi = custom_openapi
