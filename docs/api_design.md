# API Design

Add APIs only after the CLI works.

## Minimum API

```text
POST /api/jobs
POST /api/jobs/{job_id}/files
POST /api/jobs/{job_id}/run
GET /api/jobs/{job_id}
GET /api/jobs/{job_id}/report
```

## Job States

```text
created
files_uploaded
running
completed
failed
```

## Learning Task

Before implementing FastAPI, write example request and response bodies for every endpoint.
