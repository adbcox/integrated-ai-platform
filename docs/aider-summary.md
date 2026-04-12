# Aider Optimization Summary (2026-04-12)

## Manual Steps Eliminated
- Brief creation, routing, and enforcement now automated via `make aider-<class>` / `make aider-auto` and guard.
- Intake tool publishes `auto_route_command` for direct execution; micro targets remove per-task prompt writing.
- Guard artifacts now contain failure context, making retries/escalations cheap.

## Automated Enforcement Added
- Class configs enforce max files, LOC, roots, and forbidden globs; runner + guard reject violations.
- Guard now rejects forbidden directories, root overage, and diff budgets with explicit context.
- Auto-classifier + intake support reduce Codex involvement for docs/test/shell/lint flows.

## Task Classes Supported
See `config/aider_task_classes.json` and `docs/aider-automation-summary.md` for limits.

## Retry/Escalation Workflow
1. Guard failure -> examine artifact; apply suggested action.
2. Retry once after adjusting scope.
3. Escalate to Codex if failure repeats, forbidden files required, or validation fails with unclear remediation. Include guard artifact path + failure_code in summary.

## Remaining Manual/Codex Cases
- Architecture changes, schema updates, multi-root refactors beyond class limits.
- Tasks touching `config/**`, `systemd/**`, `secrets/**`, or other forbidden globs.
- Validation failures tied to external dependencies or ambiguous behavior changes.
