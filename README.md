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

Task wrappers for frequent small tasks:

```sh
./bin/fix-shell.sh
./bin/fix-python.sh
./bin/smoke-open-app.sh
./bin/aider_start_task.sh --name "task-name"
./bin/aider_handoff.sh --task-file tmp/task.md --name task-name
./bin/aider_finalize.sh
./bin/aider_capture_feedback.sh --name "task-name"
./bin/aider_export_training_jsonl.sh
./bin/aider_loop.sh --name "task-name" --goal "short objective"
```

Daily flow (dry run first):

```sh
./bin/aider_loop.sh --name "task-name" --goal "short objective" --dry-run
./bin/aider_loop.sh --name "task-name" --goal "short objective"
```

Agent-specific guardrails and workflow are documented in [AGENTS.md](/srv/platform/repos/platform-browser-operator/AGENTS.md).
Remote delegation workflow is documented in [docs/remote-codex-workflow.md](/srv/platform/repos/platform-browser-operator/docs/remote-codex-workflow.md).
Aider control workflow is documented in [docs/aider-control-workflow.md](/srv/platform/repos/platform-browser-operator/docs/aider-control-workflow.md).
