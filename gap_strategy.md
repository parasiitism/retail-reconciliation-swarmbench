# Gap Strategy

## Why Single-Agent Should Struggle

- Number of artifacts: 10 store CSV files plus 1 product catalog.
- Estimated input size: About 100 transaction rows across 10 inconsistent schemas, with many aliases for IDs, SKUs, quantities, prices, and transaction types.
- Coverage pressure: Every file has a slightly different header layout, and each store includes at least one edge case such as refunds, negative quantities, unmapped SKUs, or cross-file duplicate IDs.
- Reconciliation pressure: The final answer depends on global duplicate removal, category mapping, per-store summaries, top-SKU calculations, sorted arrays, and global totals all agreeing with one another.
- Expected failure mode: A single agent is likely to handle the common rows correctly but miss one or more schema aliases, count duplicate transactions twice, mishandle refund signs, omit an unmapped SKU, or produce internally inconsistent totals.

## Why Multi-Agent Should Succeed

- Natural subproblems: Each store file can be normalized and inspected independently, while the product catalog/header inspection can also be done separately.
- Sub-agent ownership plan: Ten store-focused workers each own one CSV export, one catalog/schema worker owns the normalization map, and a reducer owns duplicate removal plus final JSON synthesis.
- Reducer strategy: The reducer verifies that all ten store files are represented, consolidates transaction IDs by filename and row order, applies one catalog mapping, recomputes category and global totals, and checks the output schema.
- Why final synthesis is verifiable: The verifier recomputes the expected report deterministically from the input CSVs and awards partial credit for schema, store, category, duplicate, and global correctness.

## Expected Score Pattern

- Oracle expected score: 1.0
- Single-agent expected score: 0.45-0.60
- Multi-agent expected score: 0.90-1.0
- Target gap: At least 40 percentage points.

## Oracle Validation

- Oracle run completed: yes
- Oracle reward: 1.0
- Notes: Harbor oracle validation completed successfully with 1 trial, 0 exceptions, and mean reward 1.000.
