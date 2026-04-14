# Stage-3 Operator Flow (April 2026)

Stage-3 remains the production lane for literal/comment fixes. Follow this playbook for every probe so telemetry stays clean and the Stage-4 boundary remains intact.

## 1. Plan (Stage RAG-1)

- Run `bin/stage_rag1_plan_probe.py --stage stage3 --plan-id "stage3-<ticket>" --top 6 -- "<goal>"`.
- Pick the file + lines from the ranked snippets and let the helper log the entry under `artifacts/stage_rag1/usage.jsonl`.
- If you expect a literal mismatch, note it in `--notes` (shows up in the log for later analysis).

## 2. Prepare the literal template

- Copy `templates/safe-literal-probe-template.msg` to `/tmp/probe_literal.msg`.
- Replace the placeholder line with the exact literal/comment instruction (`file::<token> replace exact text ...`).
- Keep the scope ≤2 adjacent lines and a single target file.

## 3. Run the helper

```sh
make aider-micro-safe \
  AIDER_MICRO_MESSAGE_FILE=/tmp/probe_literal.msg \
  AIDER_MICRO_FILES="path/to/file.sh"
```

- Never skip the guard. If the run fails, capture the guard artifact path in your task notes.
- On success, commit immediately (or rollback if guard fails) before preparing the next probe.

## 4. Capture telemetry & regressions

- The helper already writes to `artifacts/micro_runs/events.jsonl`. Tag your plan IDs so we can match them to Stage RAG entries.
- Run `bin/stage_rag1_metrics.py --window 20` after your shift and append the summary to the task retro.
- Keep the Stage-4 regression pack (`bin/micro_lane_stage4.sh`) handy; run it whenever the guard rules change or at least once per week to ensure the rejection probes still fire.

## 5. Next data-collection period

- Goal: collect **30 Stage-3 probes** between 15–19 Apr 2026 (minimum 6 per day), each with matching Stage RAG + micro-lane entries.
- Log notable plan IDs in your PR or retro so we can filter by `stage3-*` prefixes later.
- Do **not** attempt Stage-4 tasks until we review this batch of telemetry.

Use this doc alongside `docs/aider-performance-guide.md` and `docs/safe-literal-probes.md` for the most up-to-date guardrails.

## Manager-1 automation

- Run `python3 bin/stage3_manager.py --query "<stage rag query>" --target path/to/file.sh --message "<literal instruction>" --commit-msg "short summary"`.
- The manager creates a job id, logs Stage RAG usage, writes `/tmp/stage3_job_<id>.msg`, executes `make aider-micro-safe`, classifies the result, and appends a trace row to `artifacts/stage3_manager/traces.jsonl`.
- You still need to craft the literal instruction (≤2 adjacent lines, anchored string). The manager keeps the repo clean and commits accepted diffs automatically.
