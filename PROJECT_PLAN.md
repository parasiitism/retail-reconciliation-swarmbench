# Project Plan

## Version 1: Local Reconciliation CLI

Build a local Python CLI that reconciles CSV files from one folder.

Core capabilities:

- Read CSV files
- Normalize column names
- Apply domain profile rules
- Detect duplicates
- Aggregate totals
- Write JSON report
- Run verifier

Do not use LangGraph in Version 1.

## Version 2: Generic Domain Profiles

Add support for multiple domains using profile configuration.

Domains:

- retail
- finance
- healthcare
- supply_chain

Each profile should define:

- ID fields
- amount fields
- quantity fields
- date fields
- type/status fields
- negative/refund indicators

## Version 3: LangGraph Multi-Agent Flow

Convert the reconciliation pipeline into a graph.

Graph shape:

```text
load_files
-> schema_detection
-> parallel_normalizers
-> matcher
-> reducer
-> validator
-> report_writer
```

The goal is not to make the code fancy. The goal is to make responsibilities clear.

## Version 4: FastAPI Backend

Wrap the reconciliation engine in backend APIs.

Endpoints:

```text
POST /api/jobs
POST /api/jobs/{job_id}/files
POST /api/jobs/{job_id}/run
GET /api/jobs/{job_id}
GET /api/jobs/{job_id}/report
GET /api/jobs/{job_id}/audit
```

## Version 5: Persistence And Queue

Add:

- PostgreSQL for jobs and reports
- Redis for background processing
- local storage or S3-compatible storage for uploaded files

## Version 6: Dashboard

Build a frontend that shows:

- job list
- file upload
- domain selection
- detected schema
- run status
- validation score
- matched/unmatched records
- downloadable reports

## Version 7: Production Polish

Add:

- Docker Compose
- tests
- observability
- structured logs
- metrics
- README diagrams
- demo data
- screenshots
