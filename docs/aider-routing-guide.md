# Automated Aider Routing and Retry Guide

## Inputs → Routing
1. Capture task metadata via `make local-task-intake TASK_NAME=... TASK_GOAL=... --files path1 --files path2 --auto-route`.
2. Intake auto-classifies safe tasks:
   - Docs-only → `make aider-docs-micro`.
   - Test-only or objective with "test" → `make aider-test-micro`.
   - Shell files under `shell/` → `make aider-shell-micro`.
   - Lint/format keywords → `make aider-lint-micro`.
   - Otherwise, `make aider-auto` runs `bin/aider_auto_route.py` to pick the class.
3. Intake artifact (`artifacts/intake/<task>/intake.json`) stores the recommended command (auto_route_command field).

## Preflight Verification
Run `make aider-auto` or `make aider-<class>` only after:
- Files + objective match the class limits (max files, LOC, roots).
- Forbidden globs (`config/**`, `systemd/**`, `secrets/**`, `policies/**`, `artifacts/**`) are NOT in scope.
- Acceptance criteria defined (default is guard validations).

## Guard / Validation Loop
1. `bin/aider_task_runner.py` generates JSON brief and launches `bin/aider_loop.sh --no-remote`.
2. `bin/aider_guard.py` enforces:
   - Changed files ≤ class max_files.
   - Changed roots ≤ class max_roots.
   - No forbidden globs touched.
   - Diff size ≤ max_loc.
   - Validations run automatically. Output stored in `artifacts/aider_runs/<task>.json`.
3. Guard failure codes:
   - `scope_violation` → tighten file list/roots.
   - `diff_budget` → split patch.
   - `validation_failed` → inspect logs, fix, rerun once.
   - `no_changes` → ensure patch applied before guard.
   - `validation_missing` → add commands to brief or edit class config.

## Retry vs Escalation
- **Retry once** after adjusting file list or patch scope.
- **Escalate to Codex** when:
  - Same failure repeats twice.
  - Forbidden glob is required.
  - Validation indicates systemic issue.
  - Task must touch more files/roots than allowed.
  - Aider generated partial/ambiguous edits.
Include guard artifact path + failure_code in Codex summary.

## Micro-flow Commands
| Command | Description |
|---------|-------------|
| `make aider-docs-micro` | Docs sync limited to doc files. |
| `make aider-test-micro` | Repair failing tests without touching prod scripts. |
| `make aider-shell-micro` | Tiny shell fix (default objective preset). |
| `make aider-lint-micro` | Lint/format cleanup (≤2 roots). |

Use these before resorting to manual prompts; they keep Codex out of the loop for trivial edits.

## Artifact Expectations
- Intake JSON + optional auto route command.
- Guard artifact (passed/failed) with validation results.
- MIGRATION_NOTES entry summarizing changes, guard artifact reference, and validations.

## Troubleshooting Checklist
1. Guard failure? Read the artifact first.
2. Need manual control? Run `make aider-run ... --skip-guard` only with justification logged in MIGRATION_NOTES.
3. Auto-route misclassified? Use `AIDER_CLASS` override or `--force-class` and note in intake artifact.
