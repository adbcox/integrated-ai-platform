# Remote Codex Workflow

Use this workflow when local compute is constrained and you want fast, bounded remote assistance.

## Goals
- Keep sensitive data local.
- Delegate only narrow, testable tasks.
- Validate remotely suggested changes with local checks before merge.

## Step 1: Prepare a remote-safe bundle

Create a task brief file (example: `tmp/task.md`) with:
- clear objective
- explicit constraints
- expected files to change
- validation commands

Then package sanitized context:

```sh
./bin/remote_prepare.sh \
  --task-file tmp/task.md \
  --out-dir .remote-tasks \
  --name small-refactor \
  --include browser_operator_open_app.sh \
  --include tests/run_offline_scenarios.sh \
  --include AGENTS.md
```

Output bundle:
- `.remote-tasks/<timestamp>_small-refactor/task.md`
- `.remote-tasks/<timestamp>_small-refactor/instructions.md`
- `.remote-tasks/<timestamp>_small-refactor/manifest.txt`
- `.remote-tasks/<timestamp>_small-refactor/context/*` (sanitized copies)

## Step 2: Run remote task

- Send only files from the generated bundle.
- Do not send files blocked by `policies/remote-codex-denylist.txt`.
- Ask for patch-oriented output with explicit changed files.

## Step 3: Apply and validate locally

After applying returned changes:

```sh
./bin/remote_finalize.sh --offline changed
```

Modes:
- `--offline changed` (default): `make quick` + `make test-changed-offline`
- `--offline full`: `make quick` + `make test-offline`
- `--offline skip`: `make quick` only

## Recommended task types
- boilerplate script creation
- focused refactors
- test additions
- documentation updates

## Avoid remote delegation for
- secret/config editing
- network/firewall/service exposure changes
- broad infra changes without local review plan
