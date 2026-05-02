import json
from pathlib import Path

from fastapi import FastAPI, HTTPException

from backend.app.core.catalog import load_product_catalog
from backend.app.core.job_store import create_job, get_job, update_job, utc_now
from backend.app.core.reconciliation import reconcile_many_csvs
from backend.app.core.report_writer import write_json_report
from backend.app.core.validation import validate_report

PROJECT_ROOT = Path(__file__).resolve().parents[2]

app = FastAPI(
    title="Multi-Agent Reconciliation Platform",
    version="0.1.0",
)


def model_to_dict(model) -> dict:
    if hasattr(model, "model_dump_json"):
        return json.loads(model.model_dump_json())
    return json.loads(model.json())


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/jobs/run-demo")
def run_demo_job() -> dict:
    catalog_path = PROJECT_ROOT / "sample_data" / "retail" / "product_catalog.csv"
    product_catalog = load_product_catalog(catalog_path)

    source_paths = {
        "atlanta": PROJECT_ROOT / "sample_data" / "retail" / "atlanta.csv",
        "boston": PROJECT_ROOT / "sample_data" / "retail" / "boston.csv",
    }

    report = reconcile_many_csvs(
        source_paths=source_paths,
        product_catalog=product_catalog,
    )
    validation_result = validate_report(report)

    output_path = PROJECT_ROOT / "outputs" / "reports" / "latest_report.json"
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
        catalog_path = PROJECT_ROOT / "sample_data" / "retail" / "product_catalog.csv"
        product_catalog = load_product_catalog(catalog_path)

        source_paths = {
            "atlanta": PROJECT_ROOT / "sample_data" / "retail" / "atlanta.csv",
            "boston": PROJECT_ROOT / "sample_data" / "retail" / "boston.csv",
        }

        report = reconcile_many_csvs(
            source_paths=source_paths,
            product_catalog=product_catalog,
        )
        validation_result = validate_report(report)

        output_path = PROJECT_ROOT / "outputs" / "reports" / f"{job.job_id}_report.json"
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
    report_path = PROJECT_ROOT / "outputs" / "reports" / "latest_report.json"

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
