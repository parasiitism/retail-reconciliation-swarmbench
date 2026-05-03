import json
from pathlib import Path

from pydantic import BaseModel

from backend.app.core.job_store import list_jobs
from backend.app.core.models import MultiSourceReconciliationReport, ReconciliationJob
from backend.app.core.validation import validate_report


def model_to_dict(model: BaseModel) -> dict:
    if hasattr(model, "model_dump_json"):
        return json.loads(model.model_dump_json())
    return json.loads(model.json())


def find_latest_completed_job() -> ReconciliationJob | None:
    for job in list_jobs():
        if job.status == "completed" and job.report_path:
            report_path = Path(job.report_path)

            if report_path.exists():
                return job

    return None


def load_report_from_job(job: ReconciliationJob) -> MultiSourceReconciliationReport:
    if job.report_path is None:
        raise ValueError("Cannot load dashboard report for a job without report_path")

    report_path = Path(job.report_path)
    report_data = json.loads(report_path.read_text(encoding="utf-8"))

    return MultiSourceReconciliationReport(**report_data)


def calculate_validation_score(report: MultiSourceReconciliationReport) -> int:
    validation_result = validate_report(report)

    if validation_result.is_valid:
        return 100

    error_count = sum(
        1 for issue in validation_result.issues if issue.severity == "error"
    )
    warning_count = sum(
        1 for issue in validation_result.issues if issue.severity == "warning"
    )

    score = 100 - (error_count * 25) - (warning_count * 5)
    return max(score, 0)


def build_review_queue(report: MultiSourceReconciliationReport) -> list[dict]:
    review_items: list[dict] = []

    if report.unmapped_skus:
        review_items.append(
            {
                "code": "UNMAPPED_SKUS",
                "title": "Unmapped SKUs",
                "count": len(report.unmapped_skus),
                "severity": "warning",
                "message": "Some SKUs were not found in the product catalog.",
            }
        )

    if report.duplicate_transaction_ids:
        review_items.append(
            {
                "code": "DUPLICATE_TRANSACTIONS",
                "title": "Duplicate Transactions",
                "count": len(report.duplicate_transaction_ids),
                "severity": "warning",
                "message": "Some transactions appeared in more than one source.",
            }
        )

    validation_result = validate_report(report)

    if validation_result.issues:
        review_items.append(
            {
                "code": "VALIDATION_ISSUES",
                "title": "Validation Issues",
                "count": validation_result.issue_count,
                "severity": "error",
                "message": "Some report totals need review.",
            }
        )

    return review_items


def build_dashboard_summary() -> dict:
    latest_job = find_latest_completed_job()

    if latest_job is None:
        return {
            "status": "empty",
            "message": "No completed reconciliation job found yet.",
            "metrics": {
                "net_revenue": "0.00",
                "validation_score": 0,
                "duplicates_found": 0,
                "unmapped_sku_count": 0,
                "source_count": 0,
                "transaction_count": 0,
            },
            "recent_jobs": [model_to_dict(job) for job in list_jobs()[:5]],
            "category_totals": {},
            "review_queue": [],
            "audit_events": [],
        }

    report = load_report_from_job(latest_job)

    return {
        "status": "ready",
        "latest_job": model_to_dict(latest_job),
        "metrics": {
            "net_revenue": str(report.net_revenue),
            "gross_sales": str(report.gross_sales),
            "refunds": str(report.refunds),
            "validation_score": calculate_validation_score(report),
            "duplicates_found": len(report.duplicate_transaction_ids),
            "unmapped_sku_count": len(report.unmapped_skus),
            "source_count": report.source_count,
            "transaction_count": report.transaction_count,
        },
        "recent_jobs": [model_to_dict(job) for job in list_jobs()[:5]],
        "category_totals": {
            category: model_to_dict(summary)
            for category, summary in report.category_totals.items()
        },
        "review_queue": build_review_queue(report),
        "audit_events": [model_to_dict(event) for event in report.audit_events[:10]],
    }
