# Multi-Agent Gap Strategy

This task is designed as a deterministic map-reduce benchmark.

The input naturally decomposes into ten independent store shards. Each shard has a local schema, local transaction labels, and local edge cases. A single agent must remember every schema alias and every quality rule while processing all files sequentially, which makes missed files, inconsistent refund handling, and duplicate double-counting likely.

A multi-agent system can assign one worker to each store file. Workers normalize local schemas, classify sales and refunds, and identify unmapped SKUs. A reducer then enforces the global ordering rule, removes later duplicate transaction IDs, recomputes category totals, and writes one consolidated report.

The expected failure modes are intentionally concrete:

- Missed files reduce `processed_store_count`, row counts, and global totals.
- Schema alias confusion breaks one or more stores while leaving others correct.
- Refund mistakes inflate `gross_sales` or `net_revenue`.
- Duplicate mistakes double-count `ATL-003`, `BOS-004`, `CHI-006`, or `DEN-003`.
- Missing catalog lookup leaves category totals incomplete.

The verifier gives partial credit so these failure modes are visible instead of collapsing into a single pass/fail result.
