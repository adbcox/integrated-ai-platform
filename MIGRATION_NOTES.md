# Codex Operator Migration (2026-04-12)

## What Changed
- Replaced Aider-first guardrails with Codex-led operating rules in `AGENTS.md` and README references.
- Added `docs/codex-operator-workflow.md` detailing the enforcement-oriented loop.
- Updated task/intake templates and routing docs to reflect Codex ownership of orchestration.
- Retained tactical helper scripts but reframed them as optional accelerators bounded by Codex review.

## Why
- Prior system forced every task through Aider loops, creating prompt churn and redundant approvals.
- Codex CLI upgrade makes Codex the reliable reasoning layer; repo instructions needed to match reality.
- Artifact-driven decision gates replace repeated “placeholder” prompt loops and honor local-model-first direction.

## Issues Addressed
- Excessive confirmation friction for safe read/edit steps.
- Lack of clarity separating orchestration (Codex) from implementation helpers (Aider/local models).
- Outdated references to removed workflows (`docs/aider-control-workflow.md`).

## Remaining Risks / Follow-ups
- Ensure all helper scripts referenced by the new workflow exist and remain executable (periodic `make check`).
- Continue migrating historical artifacts (`artifacts/intake/*`, escalation packets) to mention Codex ownership.
- Monitor for lingering “Aider-only” assumptions in scripts under `bin/` and clean them up incrementally.

---

## Aider Performance Optimization (2026-04-12)
- Added hard limits and failure protocol in `AGENTS.md` + `docs/aider-performance-guide.md` so Codex can run high-throughput tactical loops.
- Replaced verbose task brief with an executable template focused on objective/files/constraints/validation.
- Tightened codex-operator guidance to reject noisy Aider diffs and reference the performance playbook.
- Documented validation + evidence requirements to keep throughput high without sacrificing quality.

## Aider Automation & Cost Reduction (2026-04-12)
- Added `config/aider_task_classes.json`, automated brief generation (`bin/aider_start_task.sh`) and runner (`bin/aider_task_runner.sh`).
- `bin/aider_guard.py` now enforces scope + validations and logs artifacts. `bin/aider_loop.sh` invokes it automatically.
- Makefile exposes `make aider-<class>` targets for common flows to minimize Codex prompt work.
- New `docs/aider-automation-summary.md` summarizes enforced rules, supported classes, and escalation triggers.

## Aider Pipeline Hardening (2026-04-12)
- Added `bin/aider_lib.py` shared helpers + stricter class definitions (max roots, forbidden globs).
- `bin/aider_task_runner.py` and `bin/aider_auto_route.py` now enforce root/forbidden limits before Aider runs.
- `bin/aider_guard.py` captures failure context, rejects forbidden paths, and records artifacts with hints.
- Makefile micro targets (`aider-docs-micro`, `aider-test-micro`, etc.) plus `make aider-auto` shrink prompt overhead.
- Intake tool publishes `auto_route_command`; `docs/aider-routing-guide.md` captures the new routing + retry behavior.
