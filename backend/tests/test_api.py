from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.core.job_store import get_job


client = TestClient(app)


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
