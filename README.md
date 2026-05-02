# Multi-Agent Reconciliation Platform

This repository is a learning-first scaffold for building a scalable reconciliation platform for messy, multi-source business data.

The product goal is to ingest inconsistent files or external sources, normalize records into canonical models, reconcile totals, detect duplicates, enrich with reference data, validate outputs, and produce audit-ready reports through an API.

## Current Capabilities

- CSV connector for retail transaction files
- Schema alias mapping across heterogeneous CSV exports
- Pydantic canonical transaction and report models
- Single-source and multi-source reconciliation
- Global duplicate transaction handling
- Product catalog enrichment
- Category totals
- Unmapped SKU reporting
- Audit events for duplicate and unmapped SKU decisions
- Validation layer for report consistency
- JSON report writer
- FastAPI endpoints for demo jobs and report lookup

## Current API

Run the backend:

```powershell
python -m uvicorn backend.app.main:app --reload --reload-dir backend --reload-dir sample_data
```

Open Swagger docs:

```text
http://127.0.0.1:8000/docs
```

Available endpoints:

```text
GET  /health
POST /jobs/run-demo
POST /jobs/demo
GET  /jobs/{job_id}
GET  /jobs/{job_id}/report
GET  /reports/latest
```

## Architecture Direction

```text
multiple data sources
-> connector layer
-> schema mapping
-> canonical records
-> reconciliation core
-> duplicate handling
-> enrichment
-> validation
-> audit trail
-> report writer
-> FastAPI backend
```

Future phases:

- File upload API
- PostgreSQL job and report persistence
- Redis-backed background workers
- Frontend dashboard
- LangGraph orchestration
- Additional connectors for Excel, APIs, databases, S3, Stripe, Shopify, and ERP exports

## SwarmBench Benchmark

This repo also includes a retail reconciliation SwarmBench benchmark package in:

```text
retail-reconciliation-swarmbench/
```

The benchmark contains ten heterogeneous retail CSV shards, product catalog data, oracle artifacts, a verifier, and a LangGraph map-reduce example.

The remote repository originally contained the benchmark package at the repository root. Those root-level benchmark files are preserved for compatibility while the broader platform code lives under `backend/`, `docs/`, `frontend/`, `sample_data/`, and `retail-reconciliation-swarmbench/`.

## Resume Summary

Built a scalable AI/backend reconciliation platform prototype using FastAPI and Pydantic to normalize heterogeneous retail data, detect duplicates, enrich transactions with product catalog data, validate totals, generate audit trails, and expose reconciliation jobs through API endpoints.
