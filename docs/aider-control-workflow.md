# Aider Control Workflow

This project treats **aider as the primary control point** and uses remote Codex selectively for bounded acceleration.

## Control Loop
Single-command loop (recommended):
```sh
./bin/aider_loop.sh --name "task-name" --goal "short objective"
```

Dry-run preview:
```sh
./bin/aider_loop.sh --name "task-name" --goal "short objective" --dry-run
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

## Delegation Policy
- Default: local edits + local checks.
- Remote Codex: bounded refactors, tests, docs, boilerplate.
- Never remote: secrets, sensitive config, broad infra/network changes.

## Required Validation
- `make quick`
- `make test-changed-offline` for behavior scripts
- `make test-offline` for shared helper or harness-level changes
