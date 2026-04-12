# Codex-Led Operator Guide

This document codifies how Codex sessions run the repo end-to-end while keeping tactical helpers (Aider + local tools) in clearly bounded lanes.

## Scope & Priorities
- Canonical repo: `/srv/platform/repos/platform-browser-operator` with runtime entrypoints `browser_operator_*.sh` and helpers in `shell/common.sh`.
- Codex is the orchestration brain: assume a Codex CLI/UI session owns reasoning, planning, validation ordering, and prompt continuity until an artifact gate says otherwise.
- Aider and other tactical helpers execute only when they materially accelerate a bounded implementation step the Codex session already scoped.
- Preserve the current host/service exposure, firewall assumptions, and sanitized-remote rules unless the user explicitly authorizes a change.

## Operating Roles
**Codex (default operator)**
- Maintain the primary prompt; only reset when a deliverable artifact (validated diff, guard report, escalation packet) justifies new context.
- Gather evidence via repo reads/searches with minimal approval friction; log decisive findings in artifacts or task notes instead of asking the user to reconfirm.
- Own decision sequencing: classify → plan → inspect → edit → validate → summarize.

**Aider / tactical helpers (bounded executor)**
- Default implementation engine for routine bounded work that meets task-class limits.
- Runs must be launched via `make aider-<class>` or `bin/aider_auto_route.py`; the guard and artifacts are mandatory.
- Codex prepares input files/objectives and reviews guard output before accepting.
- Aider never plans, decomposes, or escalates on its own.

**Local model automations**
- Favor Ollama/local models for linting, codegen, and heuristics when quality is equal; keep Codex for reasoning, decomposition, and validation sequencing.
- Refresh routing/plan artifacts (`make local-model-rules-refresh`) after new evidence.

## Decision Rules
| Situation | Preferred operator | Notes |
|-----------|-------------------|-------|
| Single-file edits, investigations, documentation, validation sequencing | Codex only | Stay in the default prompt; capture context in `tmp/task-*.md` only if handing off later. |
| Mechanical multi-file rewrites with clear diff expectations | Codex orchestrates → optional `./bin/aider_loop.sh` to execute | Codex preps the task brief, reviews diffs, and resumes ownership afterwards. |
| Remote/offline delegation | Codex prepares sanitized bundle via `./bin/remote_prepare.sh` | Follow [docs/remote-codex-workflow.md](docs/remote-codex-workflow.md); Codex still controls validation ordering. |
| High-risk or policy-bound tasks | Codex stays in control and pauses only for explicit human approval | Do not insert extra confirmation prompts for routine safe steps. |

## Evidence & Prompt Discipline
- Prefer artifact-driven gates: use concrete diffs, failing test logs, or validation output as the reason to pivot, not "placeholder" responses.
- Default prompt stays loaded until a new artifact (updated task brief, escalated packet, validation report) exists; reuse the default instructions otherwise.
- Log findings inside the working note or MIGRATION summary rather than restarting tools.

## Execution Workflow
1. **Intake** – Use `./bin/local_task_intake.py` (or `make local-task-intake`) to capture task metadata. Supply `--files` to enable automatic command hints and, when safe, `--auto-route` to launch Aider without extra Codex prompts.
2. **Classify / plan** – Select a task class (bugfix-small, docs-sync, etc.), confirm files, acceptance criteria, and validations.
3. **Implement** – Use `make aider-<class>` or the micro targets (`make aider-docs-micro`, `make aider-shell-micro`, etc.) to generate briefs and run Aider with the guard.
4. **Validate** – Guard enforces scope, diff budget, forbidden globs, and validation commands. Additional manual commands only when warranted. For manual edits, still run the minimal checks (`make quick`, `make test-changed-offline`, etc.).
5. **Summarize** – Record outcomes in task notes, `artifacts/aider_runs`, and `MIGRATION_NOTES.md`. Include guard artifact paths for future Codex sessions.

Detailed workflow reference: [docs/codex-operator-workflow.md](docs/codex-operator-workflow.md)

## Remote / Escalation Guardrails
- Never share files listed in `policies/remote-codex-denylist.txt`.
- Use `./bin/remote_prepare.sh` and `./bin/remote_finalize.sh` for any out-of-band delegation; Codex stays responsible for validation sequencing and evidence capture.
- Escalated Codex runs must update `artifacts/escalations/*` via the existing helper scripts so dashboards remain truthful.

## Aider Performance Rules
**When to invoke Aider**
- Whenever a task fits a class in `config/aider_task_classes.json` (limits include max files, LOC, roots, forbidden globs).
- Documentation sweeps, targeted shell fixes, lint repairs, and test repairs are all defaulted to Aider via `make aider-<class>` or the micro targets.

**Do not invoke Aider for**
- Planning/exploration tasks, architecture decisions, cross-cutting refactors, or anything requiring human approval.
- Work that touches forbidden globs (`config/**`, `systemd/**`, `secrets/**`, etc.) unless Codex supervises manually.

**Mandatory brief contents** – Guard enforces JSON briefs generated by `bin/aider_start_task.sh` or `bin/aider_task_runner.py`. Do not hand-edit.

**Pre-flight automation**
- Runner validates files exist, enforce class budgets, and reject forbidden paths.
- `bin/aider_auto_route.py` auto-selects classes when objectives/files meet heuristics; `bin/local_task_intake.py --auto-route` can forward obvious work without Codex prompts.

**Guard enforcement**
- `bin/aider_guard.py` rejects off-scope diffs, cross-root edits, forbidden globs, and missing validations. Artifacts record failure codes + hints.

**Failure protocol**
1. After guard failure, inspect artifact, apply suggested action (split task, tighten files, rerun validations).
2. Guard failure twice → escalate to Codex (document in MIGRATION_NOTES and intake artifact).
3. Validation failure → capture logs, revert, diagnose locally before rerunning Aider.

**Anti-patterns**
- Delegating ambiguous goals (“improve X”).
- Skipping guard or validations.
- Accepting off-scope diffs.
- Touching `config/systemd/secrets` via Aider.

Detailed checklist: [docs/aider-performance-guide.md](docs/aider-performance-guide.md)

## Task Classes & Automation
- Task class definitions live in `config/aider_task_classes.json`. Each entry defines max files/LOC, default validations, allowed extra globs, and escalation triggers.
- Canonical fast-paths:
  - `make aider-bugfix-small AIDER_NAME=... AIDER_OBJECTIVE="..." AIDER_FILES="path1 path2"`
  - `make aider-refactor-narrow ...`, `make aider-test-repair ...`, etc. (see Makefile for full list)
- The wrapper `bin/aider_task_runner.sh` launches `bin/aider_start_task.sh` + `bin/aider_loop.sh` automatically with `--no-remote` for routine work.
- Task briefs are JSON files (`tmp/<task>.json`) consumed by `bin/aider_guard.py`; manual editing is rarely required.

### Guarded Execution
- `bin/aider_guard.py --task-file tmp/<task>.json` enforces scope limits, rejects off-target diffs, computes diff size, and runs the validation commands declared in the brief/class.
- `bin/aider_loop.sh` now invokes the guard automatically (unless `--skip-guard`), falling back to `remote_finalize.sh` only when necessary.
- Guard artifacts are logged under `artifacts/aider_runs/` for traceability.
- Any guard failure (scope, diff size, validation) requires immediate Codex review or task decomposition before rerunning Aider.
- Summary reference: [docs/aider-automation-summary.md](docs/aider-automation-summary.md).

### Escalation Rules (Aider ➡ Codex)
Escalate immediately when:
- Guard rejects the patch twice for the same reason.
- Required files exceed the class limit or diff size surpasses the configured budget.
- Validations fail with unclear remediation.
- Patch introduces schema/API/architecture changes (per `escalate_if` hints in the class config).
- Aider attempts to edit files outside the approved set more than once.

## Anti-Patterns To Avoid
- Spinning up new prompts every time context shifts without producing an artifact.
- Asking the user to confirm safe read/search/edit steps that already fall under these guardrails.
- Allowing Aider (or any local automation) to merge diffs without Codex review.
- Reintroducing retired `qnap_*.sh` wrappers or touching archived backups under `.compat-archive/`, `.rename-backups/`, `.host-backups/`, or `*.bak.*`.
- Changing ports/firewall/service exposure without an explicit instruction.
- Hardcoding secrets/credentials in repo files.

## File-To-Check Hints
- `browser_operator_open_app.sh`, `browser_operator_login_flow.sh`: `make quick` + applicable offline tests.
- `browser_operator_open_and_click.sh`: `make quick` + open-and-click offline scenarios.
- `browser_operator_open_container_target.sh`: `make quick` + container-target offline cases.
- `shell/common.sh`, `tests/*`: `make quick` + `make test-offline`.
- Docs-only changes: no mandatory checks but keep formatting consistent.

## Change Discipline
- Deliver one focused improvement per task and validate before starting the next.
- Document new maintenance commands in `README.md` plus any relevant `docs/*` references.
- Keep the repo clean of placeholder TODOs—convert them into actionable artifacts or remove them.
