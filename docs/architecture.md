# Architecture

## High-Level Architecture

```mermaid
flowchart TD
    A["Uploaded Files"] --> B["FastAPI Backend"]
    B --> C["File Storage"]
    B --> D["Job Queue"]
    D --> E["LangGraph Orchestrator"]
    E --> F["Schema Detection"]
    E --> G1["Normalizer Worker 1"]
    E --> G2["Normalizer Worker 2"]
    E --> G3["Normalizer Worker N"]
    G1 --> H["Matcher"]
    G2 --> H
    G3 --> H
    F --> H
    H --> I["Reducer"]
    I --> J["Validator"]
    J --> K["Report Generator"]
    K --> L["PostgreSQL"]
    K --> M["Dashboard"]
```

## First-Principles View

The platform has five core responsibilities:

1. Intake messy files.
2. Convert each row into a canonical record.
3. Match related or duplicate records.
4. Reconcile totals and mismatches.
5. Produce a validated report with an audit trail.

## Start Simple

Your first version should be:

```text
CSV folder -> Python script -> output.json
```

Only add services after the core logic is correct.
