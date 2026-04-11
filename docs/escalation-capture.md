# Escalation Capture Structure

This project captures structured artifacts for meaningful Codex escalations so local-model capability can improve over time.

## Artifact layout
For escalated tasks (`WORKFLOW_MODE` not `tactical`, or explicit trigger):
- `artifacts/escalations/<task_id>/summary.json`
- `artifacts/escalations/<task_id>/timeline.log`
- `artifacts/escalations/<task_id>/patch-notes.md`
- `artifacts/escalations/index.jsonl`

A compatibility capture record is also written to:
- `.local-model-data/<task_id>/...`

## Required captured fields (`summary.json`)
- `task_id`
- `timestamp_utc`
- `repo`
- `branch`
- `workflow_mode`
- `files_touched`
- `escalation_trigger`
- `problem_statement`
- `constraints`
- `codex_plan_summary`
- `commands_tests_run`
- `pass_fail_outcomes`
- `outcome_notes`
- `fix_pattern_root_cause`
- `reusable_local_first_heuristic`
- `completion_summary`

## Usage
Mode-driven loop (recommended):
```sh
WORKFLOW_MODE=codex-assist ./bin/aider_loop.sh --name "task-name" --goal "short objective"
```

Direct capture command (manual):
```sh
./bin/aider_capture_feedback.sh \
  --name "task-name" \
  --workflow-mode codex-failure \
  --escalation-trigger hard-failure-analysis \
  --problem "failing scenario summary" \
  --plan-summary "approach summary" \
  --fix-pattern "selector-drift"
```

Inspect recent index entries:
```sh
make escalation-index-tail
```
