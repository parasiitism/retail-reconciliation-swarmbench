# Learning Path

This is the exact order to learn and build the project.

## Phase 0: Understand The Problem

Before writing code, answer these questions in your own words:

1. What is reconciliation?
2. Why do different systems export different column names?
3. What does it mean to normalize records?
4. What is a duplicate transaction?
5. Why do we need a verifier?
6. Why can multi-agent map-reduce help?

Expected mental model:

```text
multiple messy sources -> canonical records -> matching -> reconciliation -> validation
```

## Phase 1: One CSV, One Total

Goal:

```text
Read one CSV and calculate gross sales.
```

## Your First Python CLI File

Create your first Python file here:

```text
backend/app/services/reconcile_one_file.py
```

Why this location:

```text
backend/
  because this is backend logic

app/
  because it will later become part of the backend application

services/
  because reconciliation is business logic, not an API route and not an agent yet

reconcile_one_file.py
  because your first goal is intentionally tiny: reconcile one file only
```

Do not create files in `agents/` yet.
Do not create FastAPI routes yet.
Do not create LangGraph code yet.

First write only enough code to:

```text
1. Open one CSV file from sample_data/retail/
2. Read rows using csv.DictReader
3. Multiply quantity * unit_price
4. Add the total
5. Print gross sales
```

Manual verification:

```text
1. Create one tiny CSV in sample_data/retail/store_1.csv
2. Add 2 or 3 rows where you can calculate the total by hand
3. Run backend/app/services/reconcile_one_file.py
4. Confirm the printed total matches your hand calculation
```

Rules:

- Use only Python standard library.
- Do not use pandas yet.
- Do not use LangGraph.
- Do not use classes.
- Do not build an API.

You should learn:

- `csv.DictReader`
- converting strings to numbers
- looping through rows
- printing totals

Done when:

```text
Your script prints the correct gross sales for one file.
```

## Phase 2: Product Catalog

Goal:

```text
Read products.csv and map SKU -> category.
```

You should learn:

- loading lookup dictionaries
- joining transaction rows with catalog rows
- calculating category totals

Done when:

```text
Your script prints total revenue by category.
```

## Phase 3: Refunds

Goal:

```text
Handle refund rows and negative quantities.
```

Rules:

- Sales increase gross sales.
- Refunds increase refund total.
- Net revenue = gross sales - refunds.

Done when:

```text
Your script prints gross sales, refunds, and net revenue.
```

## Phase 4: Multiple Files

Goal:

```text
Read every CSV inside a folder.
```

You should learn:

- `Path.glob`
- sorting file paths
- store-level aggregation
- global aggregation

Done when:

```text
Your script prints totals per file and global totals.
```

## Phase 5: Schema Aliases

Goal:

```text
Handle files where the same concept has different column names.
```

Example:

```text
transaction_id = txn_id = order_no
sku = item_code = product_id
quantity = qty = units
```

You should write a helper that finds the first available column from a list of aliases.

Done when:

```text
Your script can process files with different headers.
```

## Phase 6: Duplicate Detection

Goal:

```text
Detect repeated transaction IDs across files.
```

Rules:

- Report all duplicate IDs.
- Count only the first occurrence in totals.
- First occurrence means sorted filename, then row order.

Done when:

```text
Duplicate rows are excluded from totals but included in the duplicate report.
```

## Phase 7: JSON Output

Goal:

```text
Write a structured output report.
```

Output sections:

- stores
- category totals
- duplicate IDs
- global totals

Done when:

```text
Your script writes output.json.
```

## Phase 8: Verifier

Goal:

```text
Create a verifier that checks the output.
```

The verifier should:

- recompute expected totals
- read output.json
- compare actual vs expected
- print pass/fail checks
- produce a score

Done when:

```text
Wrong output gets partial score and correct output gets 1.0.
```

## Phase 9: LangGraph

Goal:

```text
Convert the linear script into a graph.
```

Nodes:

- load inputs
- one worker per file
- reducer
- validator
- report writer

Done when:

```text
The LangGraph version produces the same output as the plain Python version.
```

## Phase 10: FastAPI

Goal:

```text
Expose reconciliation as an API.
```

Endpoints:

- create job
- upload files
- run job
- get status
- get report

Done when:

```text
You can run a reconciliation job through API calls.
```

## Phase 11: Scale

Only after the basic version works, add:

- PostgreSQL
- Redis queue
- background workers
- file storage
- audit logs
- dashboard
- Docker Compose
