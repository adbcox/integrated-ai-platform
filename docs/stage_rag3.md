# Stage RAG-3 (Multi-Target Retriever)

Stage RAG-3 extends the structural retriever by pairing each lexical hit with
related files in the same directory so Stage-5 multi-file batches can pre-select
two anchors quickly.

## Key differences vs. Stage RAG-2

- Calls Stage RAG-2 under the hood but augments each result with sibling files
  sharing the same basename (e.g., `bin/foo.sh` and `bin/foo_helper.sh`).
- Emits machine-readable JSON that Manager-4 and Stage-5 consume directly.
- Logs to `artifacts/stage_rag3/usage.jsonl`, capturing both the primary and
  secondary file selections when provided.

## Usage

```sh
python3 bin/stage_rag3_plan_probe.py \
  --plan-id stage5-demo-001 \
  --selected-path bin/detect_changed_files.sh \
  --selected-lines 1-10 \
  --secondary-path bin/remote_finalize.sh \
  --secondary-lines 12-25 \
  -- "dual literal detection finalize"
```

The helper prints enriched results and records the selection for later analysis.

## Integration points

- Stage-5 manager automatically calls Stage RAG-3 for each entry.
- Manager-4 routes Stage-5 jobs through Stage RAG-3 by invoking the planner
  before dispatching Stage-5 batches.
