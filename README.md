# RevRecon - Retail Revenue Reconciliation Platform

<p align="center">
  <img src="https://img.shields.io/badge/Python-FastAPI-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python FastAPI" />
  <img src="https://img.shields.io/badge/Frontend-React%20%2B%20TypeScript-61DAFB?style=for-the-badge&logo=react&logoColor=111827" alt="React TypeScript" />
  <img src="https://img.shields.io/badge/Data-Reconciliation-7C3AED?style=for-the-badge" alt="Reconciliation" />
  <img src="https://img.shields.io/badge/Benchmark-SwarmBench-F97316?style=for-the-badge" alt="SwarmBench" />
</p>

RevRecon is a full-stack retail reconciliation platform for turning messy sales exports into normalized, auditable reconciliation reports. It is built as a practical engineering project: file ingestion, schema profiling, field mapping, deterministic reconciliation, report generation, and a dashboard for reviewing results.

![Revenue Reconciliation Dashboard](docs/assets/dashboard.png)

## Why This Project Exists

Retail transaction data rarely arrives in one clean shape. Store exports can contain different headers, missing SKU mappings, duplicate transaction IDs, refunds, negative quantities, inconsistent totals, and file formats that change over time. RevRecon is designed to make that mess reviewable and repeatable.

## What I Built

- FastAPI backend for reconciliation jobs and reports.
- React and TypeScript dashboard for uploading files and reviewing results.
- CSV profiling and schema fingerprinting for repeat file formats.
- Schema registry and field-mapping validation.
- Canonical transaction models using Pydantic.
- Deterministic reconciliation logic for sales, refunds, duplicates, SKUs, and totals.
- SQLite persistence through SQLAlchemy.
- JSON report artifacts for completed jobs.
- Tests for API behavior, schema onboarding, and mapped reconciliation.
- SwarmBench task packaging for benchmark-style evaluation.

## Architecture

```mermaid
flowchart LR
    A[CSV Upload] --> B[Schema Profiler]
    B --> C[Schema Fingerprint]
    C --> D[Schema Registry]
    D --> E[Canonical Mapper]
    E --> F[Reconciliation Engine]
    F --> G[Report Writer]
    G --> H[Dashboard Review]
    classDef input fill:#dbeafe,stroke:#2563eb,color:#1e3a8a,stroke-width:2px
    classDef process fill:#ede9fe,stroke:#7c3aed,color:#4c1d95,stroke-width:2px
    classDef output fill:#dcfce7,stroke:#16a34a,color:#14532d,stroke-width:2px
    class A input
    class B,C,D,E,F process
    class G,H output
```

## Repository Map

```text
backend/       FastAPI service, reconciliation core, connectors, report APIs
frontend/      React and TypeScript dashboard
docs/          Architecture notes and visual assets
sample_data/   Example transaction files for local testing
tests/         Backend and reconciliation test coverage
solution/      Benchmark-oriented solution material
```

## Run Locally

```powershell
pip install -r requirements.txt
uvicorn backend.app.main:app --reload
```

For the frontend:

```powershell
cd frontend
npm install
npm run dev
```

## Revision Notes

- Think in terms of data normalization before reconciliation.
- The schema registry prevents every new CSV format from becoming a new code path.
- Canonical models make reconciliation deterministic and testable.
- Fingerprinting helps recognize repeated vendor or store export formats.
- Reports should be auditable, not just visually attractive.

## Interview Talking Points

```text
I built this as a data reconciliation workflow rather than a simple CSV parser.
The important design decision is separating profiling, schema mapping, canonicalization,
reconciliation, and report generation. That makes the system easier to test and extend
when new store formats arrive.
```
