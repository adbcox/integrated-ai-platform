# Agent Operating Guide

## Scope
- Canonical repo: `/srv/platform/repos/platform-browser-operator`
- Primary runtime scripts live at repo root and are prefixed `browser_operator_*.sh`.
- Shared shell helpers live in `shell/common.sh`.
- Aider is the local control point for task orchestration.

## Objectives
- Improve maintainability and operational clarity without changing core runtime behavior.
- Prefer small, reversible edits.
- Keep network exposure and service bindings unchanged unless explicitly requested.
- Prefer bounded remote delegation only when task context is sanitized and policy-approved.

## Hard Guardrails
- Do not edit or restore archived compatibility artifacts under `.compat-archive/`, `.rename-backups/`, `.host-backups/`, or `*.bak.*` files unless explicitly asked.
- Do not reintroduce retired `qnap_*.sh` wrappers.
- Do not change default ports, firewall assumptions, or compose service exposure as part of routine maintenance.
- Do not hardcode new secrets or credentials.
- For remote delegation, do not share files matching `policies/remote-codex-denylist.txt`.

## Shell Script Conventions
- Use POSIX `sh` for existing `browser_operator_*.sh` scripts.
- Reuse `shell/common.sh` helpers for command checks and session parsing.
- Keep failure behavior explicit with clear stderr messages and non-zero exits.
- Preserve current script output shape unless the task explicitly asks to change it.

## Validation Checklist
1. Run `./validate_shell.sh` after shell-script changes.
2. Run targeted `sh -n <script>` checks for each modified script.
3. If helper logic changed, run helper smoke tests via `validate_shell.sh`.

## Fast Path For Small Tasks
1. Edit only the smallest necessary file set.
2. Run `make quick` for changed shell/python syntax checks.
3. Run `make test-changed-offline` when browser-operator behavior scripts changed.
4. Run `make test-offline` only when shared helpers or test harness changed.
5. For remote assist: prepare bundle with `./bin/remote_prepare.sh`, then validate with `./bin/remote_finalize.sh`.
6. Capture completed-task feedback locally for model improvement with `./bin/aider_capture_feedback.sh`.

## File-To-Check Hints
- `browser_operator_open_app.sh`, `browser_operator_login_flow.sh`: `make quick` + open-app offline cases.
- `browser_operator_open_and_click.sh`: `make quick` + open-and-click offline cases.
- `browser_operator_open_container_target.sh`: `make quick` + container-target offline cases.
- `shell/common.sh`, `tests/*` harness files: `make quick` + `make test-offline`.
- Docs-only changes: no mandatory checks.

Detailed mapping: [docs/validation-matrix.md](/srv/platform/repos/platform-browser-operator/docs/validation-matrix.md)
Remote workflow: [docs/remote-codex-workflow.md](/srv/platform/repos/platform-browser-operator/docs/remote-codex-workflow.md)
Aider control workflow: [docs/aider-control-workflow.md](/srv/platform/repos/platform-browser-operator/docs/aider-control-workflow.md)

## Change Discipline
- Prefer one focused refactor at a time.
- Migrate one or a few scripts, then validate before broader rollout.
- Document new maintenance commands in `README.md` when added.
