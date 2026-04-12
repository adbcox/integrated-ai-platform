# Aider Performance Guide

Codex owns orchestration. Aider exists to execute tightly scoped patches with minimal context. Follow this checklist every time.

## 1. Preflight Checklist
- ✅ Pick a task class from `config/aider_task_classes.json` (bugfix-small, refactor-narrow, test-repair, lint-fix, docs-sync, typed-cleanup, targeted-feature-patch).
- ✅ Confirm class limits: max files, max LOC, max roots, and forbidden globs.
- ✅ Objective + target files known (`AIDER_OBJECTIVE`/`AIDER_FILES` or `AIDER_AUTO_FILES`).
- ✅ Guardrails confirmed: no ports/secrets/systemd/policy files unless Codex handles manually.

## 2. Brief Template (required fields)
Preferred command path:
```sh
make aider-bugfix-small \
  AIDER_NAME="login-fix" \
  AIDER_OBJECTIVE="Stop nil session panic" \
  AIDER_FILES="browser_operator_login_flow.sh tests/mock_login_flow.sh"
```
Shortcuts: `make aider-docs-micro`, `make aider-shell-micro`, `make aider-test-micro`, `make aider-lint-micro` auto-fill objectives and classes. `make aider-auto AIDER_OBJECTIVE=... AIDER_AUTO_FILES="file1 file2"` calls the classifier.

This pipeline generates JSON briefs, enforces budgets, and runs the guard automatically.

## 3. Invocation Rules
- Use `make aider-<class>` or `./bin/aider_task_runner.sh` to avoid manual prompt building.
- Prompts stay short because the JSON brief already encodes target files/constraints.
- `bin/aider_loop.sh` automatically runs `bin/aider_guard.py` after patch application; `--skip-guard` is only for emergency fallback.

## 4. Validation & Artifacts
- Guard enforces file scope, diff size, forbidden globs, root limits, and runs validation commands. Results saved under `artifacts/aider_runs/` with failure context.
- If guard fails twice, escalate to Codex with the artifact path and failure_code.
- Manual review still occurs before commit; reference the guard artifact in summaries.

## 5. Failure Handling
| Failure | Action |
|---------|--------|
| Scope violation (extra files / forbidden globs / extra roots) | Use guard artifact to identify offenders, split task or adjust file list, rerun once. |
| Diff budget exceeded | Decompose into smaller patches; guard artifact reports lines changed. |
| Partial edit / missing files | Annotate missing pieces, shrink scope, rerun Aider or hand-edit. |
| Noisy or off-target diff | Reject immediately, tighten brief with explicit deny list or adjust class. |
| Validation failure | Save logs from guard artifact, revert patch if necessary, diagnose locally before another Aider call. |

## 6. Anti-Patterns (Never do these)
- “Improve” or “refactor” without measurable success metrics or class fit.
- Delegating debugging/planning/investigation to Aider.
- Skipping guard or validations because the diff “looks small”.
- Allowing Aider to touch `config/**`, `systemd/**`, `secrets/**`, or `policies/**` unless Codex handles manually.
- Accepting patches without referencing guard artifacts.

Keep this guide paired with `AGENTS.md` and reference it whenever Codex prepares a tactical task.
