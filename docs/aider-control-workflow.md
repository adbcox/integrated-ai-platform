# Aider Control Workflow

This project treats **aider as the primary control point** and uses remote Codex selectively for bounded acceleration.

## Control Loop
Single-command loop (recommended):
```sh
WORKFLOW_MODE=tactical ./bin/aider_loop.sh --name "task-name" --goal "short objective"
```

Dry-run preview:
```sh
WORKFLOW_MODE=codex-assist ./bin/aider_loop.sh --name "task-name" --goal "short objective" --dry-run
```

Mode check:
```sh
./bin/workflow_mode.sh show
```

Manual step-by-step loop:
1. Create task brief (aider-owned):
```sh
./bin/aider_start_task.sh --name "task-name" --goal "short objective"
```
2. Prepare remote-safe bundle when remote assist is needed:
```sh
./bin/aider_handoff.sh --task-file tmp/task-name-*.md --name task-name
```
3. Apply returned patch locally (aider-reviewed).
4. Validate locally:
```sh
./bin/aider_finalize.sh
```
5. Capture feedback for local-model improvement:
```sh
./bin/aider_capture_feedback.sh --name "task-name"
```
6. Export accumulated training corpus when needed:
```sh
./bin/aider_export_training_jsonl.sh
```

Escalated (Codex mode) runs also write structured artifacts to:
- `artifacts/escalations/<task_id>/summary.json`
- `artifacts/escalations/<task_id>/timeline.log`
- `artifacts/escalations/<task_id>/patch-notes.md`
- `artifacts/escalations/index.jsonl`

## Delegation Policy
- Default: local edits + local checks.
- Remote Codex: bounded refactors, tests, docs, boilerplate.
- Never remote: secrets, sensitive config, broad infra/network changes.

## Workflow Modes
- `tactical`: local-first tactical loop, remote Codex handoff disabled by default.
- `codex-assist`: bounded Codex assist, remote handoff enabled by default, offline checks default to `changed`.
- `codex-investigate`: deeper Codex investigation, remote handoff enabled by default, offline checks default to `full`.
- `codex-failure`: hard failure analysis with Codex, remote handoff enabled by default, offline checks default to `full`.

Per-run override remains explicit:
- `--workflow-mode <mode>` on `aider_loop.sh`
- `WORKFLOW_MODE=<mode>` env on command invocation

Operator flags still take precedence over mode defaults (`--no-remote`, `--offline`).

## Required Validation
- `make quick`
- `make test-changed-offline` for behavior scripts
- `make test-offline` for shared helper or harness-level changes
