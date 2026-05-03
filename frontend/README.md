# Frontend Dashboard

React + Vite + TypeScript dashboard for the Multi-Agent Reconciliation Platform.

## What This Frontend Does

- Loads dashboard metrics from `GET /dashboard/summary`
- Runs a demo reconciliation job through `POST /jobs/demo`
- Uploads one or more CSV files through `POST /jobs/upload-csv`
- Shows recent jobs, review queue, category revenue, audit events, and core metrics

## Why Vite Uses `/api`

The frontend calls backend routes through `/api`.

Vite rewrites:

```text
/api/dashboard/summary
```

to:

```text
http://127.0.0.1:8000/dashboard/summary
```

That proxy is configured in `vite.config.ts`.

## Run Locally

Start the backend first from the project root:

```powershell
python -m uvicorn backend.app.main:app --reload --reload-dir backend --reload-dir sample_data
```

Start the frontend from this folder:

```powershell
cd frontend
npm run dev
```

Open:

```text
http://127.0.0.1:5173
```

## Build

```powershell
npm run build
```
