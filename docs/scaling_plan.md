# Scaling Plan

## Small Scale

Use:

- local files
- Python standard library
- JSON output

## Medium Scale

Use:

- FastAPI
- PostgreSQL
- Redis queue
- background workers
- local file storage

## Large Scale

Use:

- object storage
- chunked file processing
- Polars or DuckDB
- Kubernetes
- distributed workers
- Prometheus and Grafana

## AI Scale

Add:

- LLM schema mapping
- confidence scoring
- human review workflow
- benchmark harness
- model comparison reports

## Learning Task

For every scaling feature, ask:

```text
What exact problem does this solve?
```

Do not add infrastructure just because it sounds impressive.
