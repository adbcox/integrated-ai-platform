# Aider System Freeze — Operate Mode

Effective 2026-04-12 the automation stack is considered **feature-complete for production use**.

## What This Means
- Keep using the existing task classes, auto-routing, guard, and micro targets for day-to-day development.
- Do **not** add or tweak framework layers unless repeated live runs expose a concrete failure (two+ guard failures for the same reason, or an entire task class becomes unusable).
- Codex stays in the planning/review lane only when a task exceeds class limits, needs architecture changes, or escalates after guard failures.

## Default Execution Flow
1. Capture intent (optional) via `make local-task-intake ... --files ... --auto-route`.
2. Run the suggested command or a micro target:
   - `make aider-bugfix-small ...`
   - `make aider-test-micro ...`
   - `make aider-docs-micro ...`
   - `make aider-shell-micro ...`
   - `make aider-lint-micro ...`
   - `make aider-auto ...` (classifier)
3. Let `bin/aider_guard.py` accept/reject the patch; reference the artifact in commits/notes.
4. Retry once if the guard gives an actionable hint; otherwise escalate to Codex with the artifact.

## When Codex Re-enters
- Architecture / schema / multi-root refactors that exceed class budgets.
- Guard failure repeats twice for the same task.
- Forbidden globs (config/systemd/secrets/policies/artifacts) must change.
- Ambiguous validation failures that require investigation.

Outside of those cases, continue development directly through the frozen automation.
