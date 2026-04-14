# Stage-6 preview

Stage-6 is the successor to the Stage-5 candidate lane. It keeps the same
/bin/ allowed target scope for now but upgrades the workflow so an operator can
plan and execute multiple coordinated Stage-5 jobs from one plan id and one
commit message prefix. The manifest exposes Stage-6 as a `preview` lane
(`stage6`) and documents the new `stage6-v1` stage, `manager5-v1`, and
`rag4-v1` entries alongside the existing lanes.

## What Stage-6 means

* Manager-5 (`bin/stage6_manager.py`) builds a Stage-6 plan (`--plan-id`) from a
  natural language query, assembles up to three Stage-5 entries with shared
  budgets, and optionally runs them sequentially through the Stage-5 manager.
* Each Stage-5 job keeps its own Stage-5 guard (`max_ops`, `max_total_lines`) so
  the multi-target orchestration stays bounded and auditable.
* Stage-6 commits inherit the same promotion metadata (lane, stage, manager, RAG,
  manifest) and the orchestrator logs them under `artifacts/manager5/traces.jsonl`.

## Stage RAG-4

* Stage RAG-4 (`bin/stage_rag4_plan_probe.py`) is the new retrieval component
  for Stage-6. It calls `stage_rag3_search` under the hood, then reshapes the
  output into a plan with multiple targets plus related candidates.
* The plan includes the original query, plan id, and a ranked list of targets
  with optional companion paths. In a future iteration we can expose the target
  preview (from Stage RAG-3) to the operator before every Stage-6 run.
* The planner also logs to `artifacts/stage_rag4/usage.jsonl` so we can audit
  which queries delivered which multi-target jobs.

## Manager-5 operations

1. Prepare a Stage-6 plan:

   ```sh
   python3 bin/stage6_manager.py \
     --plan-id stage6-2026-04-15 \
     --query "Coordinate documentation and script updates" \
     --commit-msg "Stage-6 hygiene fix" \
     --top 4 \
     --max-ops 2 \
     --dry-run
   ```

   The `--dry-run` option prints the Stage-5 jobs without invoking the costly
   manager.

2. When you are satisfied, rerun without `--dry-run` so Manager-5 executes each
   Stage-5 job via `bin/stage5_manager.py`.

3. Manager-5 records the plan payload plus job statuses under `artifacts/manager5/plans/{plan_id}.json`.
   The plan file now tracks lifecycle events (`planned`, `attempt_started`,
   `attempt_finished`), `current_state`, and `attempt_count` so preview
   promotion evidence is auditable without replaying raw logs.

4. When Stage RAG-4 returns several weak targets, use `--min-confidence` to keep
   only high-conviction hits and let the manager fall back gracefully via
   `--fallback-target` if necessary. All retries and refinements are recorded so
   Level 7 readiness can be audited.

5. When targeting a placeholder, use `--literal-old`/`--literal-new` and
   `--min-lines` so Stage-4 can satisfy its literal-span guard without
   raising layout errors.

3. Manager-5 always stamps the promotion metadata on every Stage-5 invocation
   and records the plan/journal to the shared trace schema.

## Experimental status

* Stage-6 currently targets the `bin/` prefix and keeps the Stage-5 regression
  pack (`bin/micro_lane_stage5.sh`). The lane is `preview` so automated dispatch
  still prefers Stage-5.
* We plan to keep Stage-6 in preview until at least three Stage-6 plans produce
  successful Stage-5 jobs and the rolling trace window clears the old failures.
* Stage-5 traces now include success/failure status, rollback markers, and
  commit hash metadata, which Manager-5 can capture in plan history and trace
  records for qualification.

## Forward plan (what must happen next)

1. **Stage-6 readiness**
   * Validate the sequential Stage-5 commits against the unified plan so the lane
     can be audited end-to-end.
   * Add tooling or documentation for operators to confirm the plan details
     before each Stage-6 run (previewing target diffs, multi-target budgets).
2. **RAG-4 maturity**
   * Track whether the `related` helper yields useful companion files and tune
     the `related-limit`/`history-window` knobs accordingly.
   * Extend the plan JSON to include line hints or preview windows when we have
     more confidence in the retrieval surface.
3. **Manager-5 stabilization**
   * Polish error handling, tracing, and environment propagation so future
     managers can reuse the Stage-6 orchestration (a potential Stage-6 candidate
     lane, Stage-7, etc.).
   * Consider adding a `--jobs-file` workflow that pairs Stage-6 with codified
     job recipes for reproducibility.

When the forward plan items above are satisfied, we can promote the Stage-6
lane to production, point the chief manifest lane to `stage6-v1`, and then start
designing its successor.
