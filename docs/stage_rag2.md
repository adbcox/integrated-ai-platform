# Stage RAG-2 (Structural Retriever)

Stage RAG-2 augments the lexical Stage RAG-1 helper with broader chunking and
light-weight structural awareness. Use it whenever you prepare a Stage-4 job or
need multi-line anchors.

## Highlights

- Indexes `bin/`, `shell/`, `docs/`, `src/`, `tests/`, and `Makefile`.
- Uses 48-line chunks (24-line overlap) and expands the preview window by
  default ±20 lines.
- Detects nearby function names or section headers and boosts matches that align
  with the query tokens.
- Optional `--json` flag emits structured output so Manager-3 and other tools can
  auto-select anchors.
- Logs operator selections under `artifacts/stage_rag2/usage.jsonl` via
  `bin/stage_rag2_plan_probe.py`.

## Typical usage

```sh
python3 bin/stage_rag2_plan_probe.py --plan-id stage4-tighten-guard --top 6 -- "tighten deploy block"
```

Pair every Stage-4 run with a Stage RAG-2 log so we can continue measuring
coverage and anchor health.
