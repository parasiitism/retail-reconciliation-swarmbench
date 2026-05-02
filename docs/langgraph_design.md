# LangGraph Design

Do not start here. Build the plain Python version first.

Once the linear pipeline works, convert it to LangGraph.

## Graph Nodes

```text
load_files
schema_detection
normalizer_worker_1
normalizer_worker_2
normalizer_worker_n
matcher
reducer
validator
report_writer
```

## Why LangGraph Helps

Single-agent or single-script failure modes:

- misses files
- mixes schemas
- forgets edge cases
- double-counts duplicates
- produces inconsistent totals

LangGraph solution:

- one worker node owns one source
- schema detection is separated
- reducer performs global reconciliation
- validator checks correctness
- report writer creates final output

## Learning Task

Draw the graph before coding it.

Then implement one node at a time.
