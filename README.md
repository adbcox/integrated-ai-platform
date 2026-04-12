# platform-browser-operator

Local browser-automation and health-check tooling for platform operations.

## Maintenance

Run shell validation after script changes:

```sh
./validate_shell.sh
```

Run combined shell + Python syntax checks:

```sh
make check
```

Run fast changed-file checks:

```sh
make quick
```

Run deterministic offline behavior tests (no NAS/API dependency):

```sh
make test-offline
```

Run only offline scenarios affected by current file changes:

```sh
make test-changed-offline
```

Prepare a remote-safe Codex task bundle:

```sh
./bin/remote_prepare.sh --task-file tmp/task.md --name small-task --include browser_operator_open_app.sh --include AGENTS.md
```

Run post-remote local validation:

```sh
./bin/remote_finalize.sh --offline changed
```

Task wrappers for frequent small tasks (Codex stays planner, Aider executes):

```sh
make aider-bugfix-small AIDER_NAME="login-fix" AIDER_OBJECTIVE="Stop nil panic" AIDER_FILES="browser_operator_login_flow.sh tests/mock_login_flow.sh"
make aider-docs-micro AIDER_NAME="docs" AIDER_OBJECTIVE="Sync runbook" AIDER_FILES="docs/runbook.md"
make aider-test-micro AIDER_NAME="tests" AIDER_OBJECTIVE="Stabilize failing tests" AIDER_FILES="tests/foo_test.sh tests/bar_test.sh"
make aider-shell-micro AIDER_NAME="shell" AIDER_OBJECTIVE="Patch helper" AIDER_FILES="shell/common.sh"
make aider-lint-micro AIDER_NAME="lint" AIDER_OBJECTIVE="Fix lint" AIDER_FILES="browser_operator.py"
make aider-auto AIDER_NAME="auto" AIDER_OBJECTIVE="Docs sync" AIDER_AUTO_FILES="docs/runbook.md docs/AGENTS.md"
```

Fast local tactical Aider entry points:

```sh
make aider-fast
make aider-hard
```

- `aider-fast` is the default tactical profile on CPU Ollama (`127.0.0.1:11535`) using `qwen2.5-coder:1.5b`, `--map-tokens 0`, and `--timeout 60`.
- `aider-hard` is explicit opt-in for heavier tasks (`qwen2.5-coder:7b`, higher map/timeout).
- Optional pass-through flags via `AIDER_ARGS`, for example:
  - `make aider-fast AIDER_ARGS="--message 'reply exactly READY'"`
  - `make aider-hard AIDER_ARGS='path/to/file.py'`

Recommended daily loop:

```sh
make local-task-intake TASK_NAME="login fix" TASK_GOAL="Stop nil session panic" TASK_CLASS="bugfix | auth" TASK_ID="login-fix" --auto-route --files browser_operator_login_flow.sh --files tests/mock_login_flow.sh
make aider-bugfix-small AIDER_NAME="login-fix" AIDER_OBJECTIVE="Stop nil session panic" AIDER_FILES="browser_operator_login_flow.sh tests/mock_login_flow.sh"
```

Agent-specific guardrails and workflow are documented in [AGENTS.md](/srv/platform/repos/platform-browser-operator/AGENTS.md).
Remote delegation workflow is documented in [docs/remote-codex-workflow.md](/srv/platform/repos/platform-browser-operator/docs/remote-codex-workflow.md).
Codex operator workflow details live in [docs/codex-operator-workflow.md](/srv/platform/repos/platform-browser-operator/docs/codex-operator-workflow.md).
High-throughput Aider usage rules live in [docs/aider-performance-guide.md](/srv/platform/repos/platform-browser-operator/docs/aider-performance-guide.md).
