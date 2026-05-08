from pathlib import Path

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.core.job_store import get_job
from backend.app.core.schema_registry import SCHEMA_REGISTRY
from backend.app.core.reconciliation import reconcile_many_csvs

client = TestClient(app)
SAMPLE_CSV_PATH = Path("sample_data/retail/atlanta.csv")


def profile_sample_csv() -> dict:
    response = client.post(
        "/schema/profile-csv",
        files={
            "file": (
                "atlanta.csv",
                SAMPLE_CSV_PATH.read_bytes(),
                "text/csv",
            )
        },
    )

    assert response.status_code == 200
    return response.json()


def test_health_check_returns_ok():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_demo_job_completed_successfully():
    response = client.post("/jobs/demo")
    payload = response.json()

    assert response.status_code == 200
    assert payload["job"]["status"] == "completed"
    assert payload["validation"]["is_valid"] is True


def test_jobs_list_returns_jobs_array():
    client.post("/jobs/demo")

    response = client.get("/jobs")
    payload = response.json()

    assert response.status_code == 200
    assert "jobs" in payload
    assert isinstance(payload["jobs"], list)
    assert len(payload["jobs"]) >= 1


def test_dashboard_summary_returns_ready_after_job():
    client.post("/jobs/demo")

    response = client.get("/dashboard/summary")
    payload = response.json()

    assert response.status_code == 200
    assert payload["status"] == "ready"
    assert "metrics" in payload
    assert "net_revenue" in payload["metrics"]
    assert "review_queue" in payload


def test_upload_rejects_non_csv_file():
    response = client.post(
        "/jobs/upload-csv",
        files={
            "files": (
                "notes.txt",
                b"hello, this is not a csv",
                "text/plain",
            )
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Only CSV files are supported right now: notes.txt"


def test_upload_accepts_multiple_csv_files():
    response = client.post(
        "/jobs/upload-csv",
        files=[
            (
                "files",
                (
                    "atlanta.csv",
                    Path("sample_data/retail/atlanta.csv").read_bytes(),
                    "text/csv",
                ),
            ),
            (
                "files",
                (
                    "boston.csv",
                    Path("sample_data/retail/boston.csv").read_bytes(),
                    "text/csv",
                ),
            ),
        ],
    )
    payload = response.json()

    assert response.status_code == 200
    assert payload["job"]["status"] == "completed"
    assert payload["uploaded_sources"] == ["atlanta", "boston"]
    assert payload["validation"]["is_valid"] is True


def test_created_job_can_be_loaded_from_store():
    response = client.post("/jobs/demo")
    payload = response.json()

    job_id = payload["job"]["job_id"]
    stored_job = get_job(job_id)

    assert stored_job is not None
    assert stored_job.job_id == job_id
    assert stored_job.status == "completed"
    assert stored_job.report_path is not None


def test_completed_job_report_can_be_fetched():
    create_response = client.post("/jobs/demo")
    create_payload = create_response.json()
    job_id = create_payload["job"]["job_id"]

    report_response = client.get(f"/jobs/{job_id}/report")
    report_payload = report_response.json()

    assert report_response.status_code == 200
    assert report_payload["job"]["job_id"] == job_id
    assert "report" in report_payload
    assert "net_revenue" in report_payload["report"]
    assert "source_reports" in report_payload["report"]


def test_unknown_job_returns_404():
    response = client.get("/jobs/not-a-real-job")

    assert response.status_code == 404
    assert response.json()["detail"] == "Job not found"


def test_schema_profile_returns_new_schema_required_before_registration():
    SCHEMA_REGISTRY.clear()

    payload = profile_sample_csv()

    assert payload["profile"]["filename"] == "atlanta.csv"
    assert payload["profile"]["column_count"] == 6
    assert payload["schema_resolution"]["match_type"] == "new_schema_required"
    assert payload["schema_resolution"]["schema"]["field_mapping"] == {}


def test_schema_register_then_profile_returns_exact_match():
    SCHEMA_REGISTRY.clear()

    profile_payload = profile_sample_csv()
    profile = profile_payload["profile"]

    register_response = client.post(
        "/schema/register",
        json={
            "profile": profile,
            "schema_name": "Atlanta Retail Export",
            "company_name": "Demo Retail Co",
            "field_mapping": {
                "transaction_id": "transaction_id",
                "transaction_date": "date",
                "sku": "sku",
                "quantity": "quantity",
                "unit_price": "unit_price",
                "transaction_type": "transaction_type",
            },
        },
    )
    register_payload = register_response.json()

    assert register_response.status_code == 200
    assert register_payload["status"] == "registered"
    assert register_payload["mapping_validation"]["is_valid"] is True
    assert register_payload["schema"]["status"] == "active"
    assert register_payload["schema"]["schema_name"] == "Atlanta Retail Export"

    second_profile_payload = profile_sample_csv()

    assert second_profile_payload["schema_resolution"]["match_type"] == "exact_match"
    assert (
        second_profile_payload["schema_resolution"]["schema"]["field_mapping"]["sku"]
        == "sku"
    )


def test_schema_register_rejects_invalid_mapping():
    SCHEMA_REGISTRY.clear()

    profile_payload = profile_sample_csv()

    response = client.post(
        "/schema/register",
        json={
            "profile": profile_payload["profile"],
            "schema_name": "Broken Retail Export",
            "field_mapping": {
                "transaction_id": "transaction_id",
                "transaction_date": "date",
                "sku": "sku",
                "quantity": "quantity",
                "unit_price": "missing_price_column",
            },
        },
    )
    payload = response.json()
    issue_types = {
        issue["type"]
        for issue in payload["detail"]["issues"]
    }

    assert response.status_code == 400
    assert payload["detail"]["is_valid"] is False
    assert "mapped_columns_not_found_in_csv" in issue_types


def test_reconciliation_uses_explicit_field_mapping(tmp_path):
    csv_path = tmp_path / "company_a.csv"
    csv_path.write_text(
        "\n".join([
            "Order No,Txn Date,Product Code,Qty Sold,Price,Kind",
            "A-001,2026-01-01,SKU-1001,2,5.00,sale",
            "A-002,2026-01-02,SKU-1001,-1,5.00,refund",
        ]),
        encoding="utf-8",
    )

    report = reconcile_many_csvs(
        source_paths={"company_a": csv_path},
        product_catalog={"SKU-1001": "electronics"},
        source_field_mappings={
            "company_a": {
                "transaction_id": "Order No",
                "transaction_date": "Txn Date",
                "sku": "Product Code",
                "quantity": "Qty Sold",
                "unit_price": "Price",
                "transaction_type": "Kind",
            }
        },
    )

    assert report.transaction_count == 2
    assert report.sale_count == 1
    assert report.refund_count == 1
    assert str(report.gross_sales) == "10.00"
    assert str(report.refunds) == "5.00"
    assert str(report.net_revenue) == "5.00"
