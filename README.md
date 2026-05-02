# Multi-Agent Reconciliation Platform

This repository is a learning-first scaffold for building a multi-agent reconciliation platform from scratch.

The goal is to build one platform that can reconcile messy, heterogeneous data across multiple domains:

- Finance reconciliation
- Payment settlement
- Retail transaction reporting
- Supply-chain data cleanup
- Healthcare claims processing
- Insurance document reconciliation
- Enterprise ETL validation
- AI agent benchmarking
- Data quality automation
- LLM evaluation infrastructure

## Product Idea

Users upload multiple inconsistent files. The platform detects schemas, normalizes records into a canonical model, matches duplicates or related records, reconciles totals, validates the result, and produces a report with an audit trail.

```text
messy files
-> schema detection
-> normalization
-> matching
-> reduction
-> validation
-> report + audit trail
```

## Important Learning Rule

Do not start with agents, LangGraph, FastAPI, Docker, or a frontend.

Start with one small Python script that reads one CSV file and prints one total. Then add one concept at a time.

## Recommended Build Order

1. Plain Python CLI
2. Canonical record model
3. Domain profiles
4. Multi-file reconciliation
5. Verifier and scoring
6. LangGraph orchestration
7. FastAPI backend
8. Job queue and database
9. Frontend dashboard
10. Docker and deployment

## Repository Structure

```text
multi-agent-reconciliation-platform/
|-- README.md
|-- LEARNING_PATH.md
|-- PROJECT_PLAN.md
|-- .gitignore
|-- docs/
|   |-- architecture.md
|   |-- domain_profiles.md
|   |-- data_model.md
|   |-- api_design.md
|   |-- langgraph_design.md
|   `-- scaling_plan.md
|-- backend/
|   |-- README.md
|   |-- app/
|   |   |-- api/
|   |   |-- agents/
|   |   |-- core/
|   |   `-- services/
|   `-- tests/
|-- frontend/
|   `-- README.md
`-- sample_data/
    |-- retail/
    |-- finance/
    |-- healthcare/
    `-- supply_chain/
```

## First Thing To Build

Start with `LEARNING_PATH.md`.

Your first implementation task is intentionally tiny:

```text
Read one retail CSV file and calculate gross sales.
```

Only after that works should you add:

- product catalog lookup
- refunds
- multiple files
- schema aliases
- duplicate detection
- JSON output
- verifier
- LangGraph

## What This Project Should Become

The final version should look like an AI infrastructure and backend system:

```text
FastAPI backend
+ LangGraph multi-agent orchestration
+ canonical data model
+ domain profile engine
+ reconciliation validator
+ audit trail
+ downloadable reports
+ dashboard
```

## Resume Target

When complete, this can become a strong AI Infra + Backend resume project:

```text
Built a multi-agent reconciliation platform using FastAPI, LangGraph, Docker, PostgreSQL, and Redis to normalize heterogeneous datasets across finance, retail, healthcare, and supply-chain domains; implemented schema-detection agents, parallel normalizer workers, reducer validation, audit trails, and downloadable reconciliation reports.
```
