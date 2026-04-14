Stage RAG-1 Rollout Plan
========================

Purpose
-------
Stage RAG-1 is now the default planning surface before any Stage-3 or Stage-4
literal probe. The lexical retriever helps identify the exact file + anchor,
while new logging/metrics keep the existing micro lane intact.

Workflow
--------
1. **Plan** – Run `bin/stage_rag1_plan_probe.py --stage stage4 --top 6 -- "<goal>"`,
   review the ranked snippets, and log the file/line range you intend to edit.
2. **Probe** – Craft/update the literal message (per
   [safe-literal-probes](safe-literal-probes.md)) and run the probe via
   `make aider-micro-safe` or the Stage-4 boundary harness. The Stage-4 script
   now auto-runs `bin/stage_rag1_plan_probe.py` and passes the resulting
   `plan_id` into `bin/aider_micro.sh`, so planning logs and preflight telemetry
   stay linked.
3. **Measure** – After a probe battery, execute
   `bin/stage_rag1_metrics.py --window 40` to summarize:
   - how many Stage-4 planning events were logged, and
   - how often `literal_replace_missing_old`, `missing_file_ref`, `missing_anchor`,
     `literal_shell_risky`, or `prompt_contract_rejection` surfaced in either the
     guard metadata or the micro-lane preflight log (`artifacts/micro_runs/events.jsonl`).

Because logging lives under `artifacts/stage_rag1/usage.jsonl` and
`artifacts/micro_runs/events.jsonl`, no new tracked files are added to the repo;
results are easy to export into probe write-ups or
regression checklists.

Validation Questions
--------------------
- Did every Stage-4 probe run have a matching Stage RAG planning log entry?
- Are literal-miss or anchor failure rates trending downward compared with the
  previous battery (baseline script output is included in PR summaries)?
- Do we have enough evidence to consider RAG-2 embeddings? (Only after the
  lexical helper plus guard telemetry show diminishing returns.)

This document pairs with `docs/stage_rag1.md` (tool reference) and the new
planning section in `docs/safe-literal-probes.md`.

Next Data-Collection Window
---------------------------
- Collect **30 Stage-3 probes between 15–19 Apr 2026** (at least six per day).
- Each probe must have matching entries in `artifacts/stage_rag1/usage.jsonl` and `artifacts/micro_runs/events.jsonl`.
- After every batch, run `python3 bin/stage_rag1_metrics.py --window 20` and paste the summary into your PR/retro notes.
- Do not reconsider Stage-4 promotions until this batch is complete and reviewed.
