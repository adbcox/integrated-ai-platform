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
make aider-smart   # 32B path (requires OLLAMA_API_BASE_32B)
make aider-smart-status  # ping the configured 32B endpoint before smart runs

# Opt-in Stage 3 micro profile:
# make aider-fast AIDER_ARGS="--micro-profile"

# Micro lane (tiny autonomous edits)

```sh
make aider-micro-help
make aider-micro-safe \
  AIDER_MICRO_MESSAGE="shell/common.sh::extract_session add guard for blank ids" \
  AIDER_MICRO_FILES="shell/common.sh"
```

- rejects vague prompts and doc edits before launching aider
- message must anchor each file using `<basename>::<token>` syntax
- enforces clean tree, ≤2 code-adjacent files, automatic quick checks
- classifies failures (`dirty_tree`, `weak_prompt`, `scope_violation`, etc.) for faster triage
```

- `aider-fast` is the default tactical profile on CPU Ollama (`127.0.0.1:11535`) using `qwen2.5-coder:1.5b`, `--map-tokens 0`, and `--timeout 60`.
- `aider-fast` now pings `OLLAMA_API_BASE` (default `http://127.0.0.1:11535`) before launching; export `AIDER_LOCAL_SKIP_PING=1` only if you already manage connectivity.
- `aider-hard` is explicit opt-in for heavier tasks (`qwen2.5-coder:7b`, higher map/timeout).
- `aider-smart` routes to the 32B endpoint (set `OLLAMA_API_BASE_32B` or pass `--api-base`). Always run `make aider-smart-status` first so you know the endpoint is reachable.
- Optional pass-through flags via `AIDER_ARGS`, for example:
  - `make aider-fast AIDER_ARGS="--message 'reply exactly READY'"`
  - `make aider-hard AIDER_ARGS='path/to/file.py'`
  - `make aider-smart AIDER_ARGS='--message "audit README" docs/aider-performance-guide.md'`

### Micro lane (tiny autonomous edits)

Use the new helper when you want the local model to attempt a very small patch (one or two files) with strict guard rails:

```sh
make aider-micro-safe \
  AIDER_MICRO_MESSAGE="Add a docstring to foo()" \
  AIDER_MICRO_FILES="src/foo.py"
```

Constraints:
- Requires a clean working tree (no staged or unstaged changes).
- Supports at most two repo-relative files.
- Automatically runs `make quick`.
- Fails if aider touches any file outside the provided list or if nothing changes.
- Message must explicitly name the file(s) and give a concrete action (e.g., "In shell/common.sh, add docstring to run_cmd" instead of "document run_cmd").
- Code-centric files only (`shell/`, `src/`, `tests/`, `bin/`, `config/`, `Makefile`). Markdown/README/doc changes must use the normal docs workflows.

Good micro tasks:
- `make aider-micro-safe AIDER_MICRO_MESSAGE="In shell/common.sh, add a guard that returns early when cmd is empty." AIDER_MICRO_FILES="shell/common.sh"`
- `make aider-micro-safe AIDER_MICRO_MESSAGE="In tests/mock_login_flow.sh, replace literal 'SUCCESS' with 'PASS' in the final echo." AIDER_MICRO_FILES="tests/mock_login_flow.sh"`

Verify the Stage 3 lane at any time with:

```
make micro-lane-regression
```

Bad (rejected) micro tasks:
- `make aider-micro-safe AIDER_MICRO_MESSAGE="Clarify README wording." AIDER_MICRO_FILES="README.md"`
- `make aider-micro-safe AIDER_MICRO_MESSAGE="Touch docs to mention benchmarking." AIDER_MICRO_FILES="docs/aider-performance-guide.md"`

Benchmark/report helpers:

```sh
make aider-bench-report      # table of recent runs with model/profile info
make aider-bench-compare SCENARIO=single-file-edit
make aider-bench-models      # show fast/hard/smart defaults
```

Recommended daily loop:

```sh
make local-task-intake TASK_NAME="login fix" TASK_GOAL="Stop nil session panic" TASK_CLASS="bugfix | auth" TASK_ID="login-fix" --auto-route --files browser_operator_login_flow.sh --files tests/mock_login_flow.sh
make aider-bugfix-small AIDER_NAME="login-fix" AIDER_OBJECTIVE="Stop nil session panic" AIDER_FILES="browser_operator_login_flow.sh tests/mock_login_flow.sh"
```

Agent-specific guardrails and workflow are documented in [AGENTS.md](/srv/platform/repos/platform-browser-operator/AGENTS.md).
Remote delegation workflow is documented in [docs/remote-codex-workflow.md](/srv/platform/repos/platform-browser-operator/docs/remote-codex-workflow.md).
Codex operator workflow details live in [docs/codex-operator-workflow.md](/srv/platform/repos/platform-browser-operator/docs/codex-operator-workflow.md).
High-throughput Aider usage rules live in [docs/aider-performance-guide.md](/srv/platform/repos/platform-browser-operator/docs/aider-performance-guide.md).
