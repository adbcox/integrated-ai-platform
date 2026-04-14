# Stage-5 Promotion & Validation Plan (April 2026)

## Candidate class

- **Scope:** up to two literal/comment edits across separate files, each 3–8
  contiguous lines, operated through Stage-4 guardrails.
- **Orchestration:** `bin/stage5_manager.py` sequences the entries, runs Stage
  RAG-3 for each plan, enforces per-entry Stage-4 budgets (via
  `--max-total-lines`) and aborts if the combined add+delete exceeds 20 lines.
- **Rollback:** manager snapshots `HEAD`, restores automatically on any failure,
  and commits once at the end with the supplied message. Trace rows now include
  per-operation diff metadata for audit.

## Retrieval expectations (Stage RAG-3)

- Hybrid pipeline built atop Stage RAG-2.
- For each ranked chunk, adds:
  - sibling files matching the basename (`--related-limit`).
  - co-edited files discovered from the last `--history-window` commits (tagged
    with `"source": "git_history"` in the JSON payload).
- Planner (`bin/stage_rag3_plan_probe.py`) records both primary and secondary
  selections in `artifacts/stage_rag3/usage.jsonl`.

## Manager-4 responsibilities

- Stage auto-selection (Stage-3/4/5) still keyed off literal span thresholds.
- When `--stage stage5` (or auto detects via `--secondary-*` flags) Manager-4:
  - builds a temporary JSON batch from the CLI literals,
  - forwards it to Stage-5 manager,
  - logs the resolved batch path in `artifacts/manager4/traces.jsonl`.
- Optional knobs:
  - `--stage5-primary-max-total-lines` to tighten per-entry budgets.
  - `--secondary-*` family (query/target/message/lines/notes/top/window/max
    lines) for the follow-on literal.

## Minimal validation for each promotion attempt

1. **Retrieval smoke:** run
   `python3 bin/stage_rag3_search.py --top 3 --related-limit 2 --history-window 10 "<goal>"`
   and confirm JSON contains both `"sibling"` and `"git_history"` references.
2. **Manager auto-batch dry run:** invoke Manager-4 with `--stage stage5`,
   pointing to two safe literal templates but add `--stage stage5 --commit-msg
   "dry-run"` and abort before worker dispatch (e.g., use harness stub) to
   verify batch construction and trace logging.
3. **Full Stage-5 execution:** run a dual literal edit touching two shell/bin
   files (one of them `bin/aider_capture_feedback.sh` per guard telemetry) and
  confirm a single commit plus Stage-5 trace entry.

## Remaining work before production

- Expand Stage-5 to optionally cover three files (bounded by 30 total lines).
- Add automated regression that replays historical dual-literal tasks via the
  new manager.
- Evaluate whether Stage RAG-3 needs embeddings for cross-directory partners
  once we observe more than ~10% miss rate in real probes.
