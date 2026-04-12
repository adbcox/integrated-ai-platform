# Codex Operator Workflow

This document replaces the Aider-centric control assumptions and describes how Codex remains the primary orchestrator while tactical helpers are invoked only when they materially accelerate execution.

## Control Principles
- **Codex owns orchestration** – planning, evidence gathering, decision gates, and validation sequencing stay inside the Codex session unless an artifact requires escalation.
- **Artifacts drive prompt changes** – stay on the default prompt until a new artifact (task brief, validation log, escalation packet) is generated; only then consider switching to a specialized prompt.
- **Low-friction reads/writes** – default to immediate repo inspection and small edits without additional confirmation; approvals are only needed for destructive/system-level actions per repo guardrails.
- **Evidence > placeholder loops** – convert findings into diffs, validation logs, or task notes; avoid “let’s revisit later” without producing a concrete artifact.

## Standard Loop
1. **Intake** (optional) – `./bin/local_task_intake.py` or `make local-task-intake` captures metadata and suggested workflow mode. Codex keeps ownership even if the recommended mode is `codex-assist`.
2. **Plan** – pick a task class (bugfix-small, refactor-narrow, etc.), list files, and define acceptance criteria.
3. **Implement** – run `make aider-<class> AIDER_NAME=... AIDER_OBJECTIVE=... AIDER_FILES="..."` to auto-generate the brief and launch `bin/aider_loop.sh`.
4. **Validate** – the guard inside `aider_loop` enforces file scope, diff size, and validation commands from the class definition. No manual test selection is needed unless the task demands extras.
5. **Summarize** – update task notes or `MIGRATION_NOTES.md` with decisions, remaining risks, and validation evidence (`artifacts/aider_runs/*.json`).

## Tactical Helper Usage (Aider, etc.)
- Follow [docs/aider-performance-guide.md](aider-performance-guide.md) and [docs/aider-routing-guide.md](aider-routing-guide.md).
- Prefer automation: `make aider-<class>`, micro targets, or `make aider-auto` handle brief generation + guard.
- Guard output (artifact) is the acceptance gate. Record artifact paths in summaries.
- After an Aider run, capture feedback if needed via `./bin/aider_capture_feedback.sh`.
- Never bypass guard unless explicitly logged in MIGRATION_NOTES.

## Remote Delegation
- Follow [docs/remote-codex-workflow.md](remote-codex-workflow.md) with Codex preparing bundles via `./bin/remote_prepare.sh` and validating with `./bin/remote_finalize.sh`.
- Denylist enforcement: never include files listed in `policies/remote-codex-denylist.txt`.
- Escalation artifacts (`artifacts/escalations/*`) must be updated when remote Codex runs occur.

## Mode Selection
- Rely on `policies/local-routing-rules.json` + `./bin/select_workflow_mode.py` for historical guidance, but Codex decides final mode based on task complexity and artifact readiness.
- `tactical` remains default; `codex-assist` or `codex-investigate` should only be used when heavier automation or investigation is justified.

## Anti-Patterns
- Restarting prompts repeatedly instead of producing artifacts.
- Asking the user to reconfirm safe actions already covered by guardrails.
- Allowing tactical helpers to apply diffs without Codex review or guard artifacts.
- Ignoring validation discipline or failing to record guard outcomes.
- Sending tasks that exceed class limits to Aider instead of decomposing or escalating.

## Validation Matrix Reference
Use [docs/validation-matrix.md](validation-matrix.md) when selecting tests/checks to keep the workflow predictable.
