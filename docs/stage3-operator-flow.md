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

## 3. Run Manager-3 (auto routes Stage 3/4)

```sh
python3 bin/manager3.py \
  --query "<stage rag query>" \
  --target path/to/file.sh \
  --message "<literal instruction>" \
  --commit-msg "short summary"
```

- Manager-3 inspects the literal span. ≤2 lines stay in Stage 3, longer blocks
  (3–8 lines) route to `bin/stage4_manager.py` with Stage RAG-2 planning.
- You can still call `bin/stage3_manager.py` directly when you need the legacy
  path; the rest of this section applies to both managers unless noted.

- The manager creates a unique job id, logs Stage RAG-1 usage, writes the `/tmp/stage3_job_<id>.msg` payload, runs `make aider-micro-safe`, and records the outcome/trace row automatically.
- Built-in preflights now skip harness files (`bin/aider_micro.sh`, `bin/preflight_normalization_guard.sh`, etc.), detect stale literals, and validate prompt shape before the worker launches.
- **Avoid using the word “comment” unless you are editing actual comment lines.** The guard treats any prompt mentioning “comment” as a comment-only probe; if you’re changing shell code, say “literal” instead.
- If the manager reports `prompt_shape_invalid`/`comment_scope_preflight`, rewrite the instruction (or route to Codex) instead of forcing a run.
- Accepted diffs are committed immediately; failed runs leave the repo clean so you can prepare the next probe.

## 4. Capture telemetry & regressions

- The helper already writes to `artifacts/micro_runs/events.jsonl`. Tag your plan IDs so we can match them to Stage RAG entries.
- Run `bin/stage_rag1_metrics.py --window 20` after your shift and append the summary to the task retro.
- Keep the Stage-4 regression pack (`bin/micro_lane_stage4.sh`) handy; run it whenever the guard rules change or at least once per week to ensure the rejection probes still fire.

## 5. Next data-collection period

- Goal: collect **30 Stage-3 probes** between 15–19 Apr 2026 (minimum 6 per day), each with matching Stage RAG + micro-lane entries.
- Log notable plan IDs in your PR or retro so we can filter by `stage3-*` prefixes later.
- Do **not** attempt Stage-4 tasks until we review this batch of telemetry.

Use this doc alongside `docs/aider-performance-guide.md` and `docs/safe-literal-probes.md` for the most up-to-date guardrails.

## Manager quick reference

- The CLI above is the default Stage-3 lane. Use manual `make aider-micro-safe` only when debugging the manager or when a harness/manager change has been routed to Codex.
- Keep literal prompts ≤2 adjacent lines, provide exact `file::<token>` anchors, and avoid placeholder tokens such as `<OLD_TEXT>`.
- If you truly need a comment-only probe, make sure both the old and new literal strings begin with comment characters (`#`, `//`, etc.) so the guard accepts the scope.
