# Aider Automation Summary

## Manual Steps Removed
- Brief creation is now automated via `bin/aider_start_task.sh`/`bin/aider_task_runner.sh`; no hand editing of Markdown templates.
- Class-specific make targets (`make aider-<class>`) remove repetitive prompt composition.
- Scope validation + test execution are enforced by `bin/aider_guard.py` inside `bin/aider_loop.sh`.
- Acceptance evidence is recorded automatically under `artifacts/aider_runs/`.

## Automated Enforcement
- File count / diff-size budgets per class from `config/aider_task_classes.json`.
- Allowed file patterns and out-of-scope protections enforced by the guard.
- Validation commands run on every guard invocation; failure stops the loop.
- Rejection gate ensures only approved files changed before feedback capture.

## Supported Task Classes
| Class | Max Files | Max LOC | Default Validations |
|-------|-----------|---------|---------------------|
| bugfix-small | 2 | 100 (1 root) | `make quick`, `make test-changed-offline` |
| refactor-narrow | 3 | 160 (≤2 roots) | `make quick`, `make test-changed-offline` |
| test-repair | 3 | 130 (≤2 roots) | `make quick`, `make test-offline` |
| lint-fix | 4 | 60 (≤2 roots) | `make quick` |
| docs-sync | 4 | 160 (docs only) | `make quick` |
| typed-cleanup | 3 | 140 (1 root) | `make quick` |
| targeted-feature-patch | 3 | 150 (≤2 roots) | `make quick`, `make test-changed-offline` |

## Mandatory Escalation to Codex
- Guard fails twice for the same task.
- Change set requires more files, lines, or roots than the class allows.
- Validations fail with unclear remediation or external dependencies.
- Architecture/API/schema adjustments emerge mid-task.
- Aider touches files outside the approved set or hits forbidden globs.
- Binary diffs or generated artifacts appear in `git diff`.

Use this summary when deciding whether a task can stay on the automated path or needs Codex planning/review.
