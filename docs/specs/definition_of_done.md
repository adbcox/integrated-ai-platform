# Definition of Done — Canonical Coding-Run Acceptance Policy

**Spec ID**: DOD-SPEC-1  
**Status**: active  
**Date**: 2026-04-21  
**Phase linkage**: Phase 0 (governance_source_of_truth_reconciliation), Phase 1 (runtime_contract_foundation)  
**Authority sources**: ADR-0001 through ADR-0007, governance/execution_control_package.schema.json, governance/cmdb_lite_registry.v1.yaml, P0-01-AUTHORITY-SURFACE-INVENTORY-1

---

## Purpose

This document specifies the canonical **Definition of Done** for all coding runs in the integrated AI platform. A coding run is "done" only when every gate in this definition has been satisfied. Partial completion does not count.

The machine-readable form is `governance/definition_of_done.v1.yaml`. This document is the human-readable companion.

---

## Source of Authority

The Definition of Done derives its authority from:

- **ADR-0006** (artifact bundle) — what constitutes a valid artifact output
- **ADR-0007** (autonomy scorecard) — `governance_conformance` dimension requires DoD compliance
- **ADR-0003** (workspace contract) — rollback semantics map to workspace `failed` state
- **governance/execution_control_package.schema.json** — every package declares its own validation_order and rollback_rule; this DoD is the meta-policy that governs those declarations

---

## The Done Condition

A coding run is **done** when **all** of the following are true:

1. Every file in `allowed_files` that was supposed to be created/modified exists on disk
2. No file outside `allowed_files` was touched
3. All `artifact_outputs` exist at their declared paths, parse successfully, and contain their declared `artifact_id`
4. All steps in `validation_order` were executed in order and passed
5. `make check` passed
6. `escalation_status` was explicitly reported in the exec output
7. A git commit was produced

If any condition is false, the run is **not done**.

---

## Required Artifacts

### On-disk changes

Every file created or modified must appear in the package's `allowed_files` list. Touching any file outside this list is a hard stop and triggers rollback, even if the change is beneficial.

### Runtime artifacts

Every entry in `artifact_outputs` must be produced at its declared path. An artifact that exists but cannot be parsed (JSON/YAML load error) is treated as absent and triggers a hard stop.

### Artifact ID

Every produced artifact must contain an `artifact_id` field matching the value declared in `artifact_outputs[].artifact_id`. A mismatch is a hard stop.

---

## Required Validation

### Validation order

Steps must run in the order declared in `validation_order`. Skipping a step is not permitted, even if the exec terminal believes it is safe to do so.

### make check

`make check` is mandatory for every package, regardless of label. It is always the final step. A run that skips `make check` is not done.

### Package-specific tests

If a seam test file is declared in `allowed_files`, that test suite must pass. All tests must pass — a partial pass is not acceptable.

### Real paths

Validation must run against real repository paths. A test that only exercises `tmp_path` fixtures does not satisfy the done condition unless it also exercises the actual artifact path (e.g., via `test_runner_script_executes`).

---

## Rollback Semantics

### Slice-only rollback

On any hard stop, remove only the files in `rollback_rule.remove_on_failure`. Do not remove, restore, or modify any pre-existing file.

### Preserve unrelated changes

`rollback_rule.preserve_always` lists files that must never be touched. Rollback must not alter these files, even if they were read during the run.

### Recovery

After rollback, a recovery attempt reuses the same `package_id` with a recovery note:

```
{package_id} (recovered): {one-line description of what was fixed}
```

---

## Telemetry Completeness

Every exec output must include these fields. Omitting any required field is a defect in the telemetry:

| Field | Required | Hard stop if omitted |
|-------|----------|---------------------|
| `package_id` | yes | yes |
| `label` | yes | yes |
| `files_touched` | yes | no |
| `artifacts_produced` | yes | no |
| `validations_run` | yes | no |
| `validation_results` | yes | yes |
| `escalation_status` | yes | yes |
| `hard_stops_hit` | yes | no |
| `residual_notes` | yes | no |
| `commit_id` | yes | no |

`escalation_status` must be one of: `NOT ESCALATED`, `ESCALATED` (with reason).

`commit_id` must be the actual git SHA. If the run was rolled back without committing, report `NONE (rollback)`.

---

## Escalation Handling

### When to escalate

Escalation is required when any of these is evidenced:
- A forbidden file would need to be modified
- The scope cannot be satisfied within `allowed_files`
- A required grounding input is missing after one recovery attempt
- A LOCAL-FIRST run exhausts both primary and fallback model attempts
- A scope violation is detected mid-run that cannot be corrected

### How to escalate

1. Stop execution immediately
2. Report `escalation_status: ESCALATED` with the exact blocker and evidence
3. Execute rollback per `rollback_rule.remove_on_failure`
4. Do not take further autonomous action until the control window responds

### Claude rescue rule

If a LOCAL-FIRST package encounters a blocker, the exec terminal must **escalate to the control window** — it must not silently switch to SUBSTRATE (Claude) execution. SUBSTRATE is only authorized when the package label is `SUBSTRATE`.

---

## Acceptance Rules by Label

### SUBSTRATE

SUBSTRATE work is explicitly authorized for Claude Code. Claude implements directly without a LOCAL-FIRST attempt.

**Authorized scope**: governance, schema, ADR, contract, registry, spec, and template work.

**Done condition**: all `allowed_files` created/updated, all `artifact_outputs` exist and parse, all `validation_order` steps pass, `make check` passes, `escalation_status` reported, commit produced.

**Hard constraint**: SUBSTRATE packages must not implement runtime execution logic. If the objective requires it, the package must be re-labeled LOCAL-FIRST or split.

### LOCAL-FIRST

LOCAL-FIRST work must attempt Aider/Ollama execution first, even when SUBSTRATE capability is available.

**Model routing**: use `model_profiles` from `governance/cmdb_lite_registry.v1.yaml`. Default is `fast`; `hard` is permitted for complex tasks.

**File scope**: max 5 files per run (per model profile `max_file_scope`). Larger scope must be split or escalated.

**Fallback**: if the `fast` profile fails, one attempt with `hard` is permitted. If both fail, escalate — do not route to SUBSTRATE.

**Done condition**: Aider/Ollama execution completes, all `artifact_outputs` exist and parse, `make check` passes, `escalation_status` reported, commit produced.

### ESCALATION

ESCALATION runs require explicit control-window approval before execution begins.

**Approval evidence**: the exec output must reference the control window approval. An ESCALATION run without approval evidence is a scope violation.

**File scope**: only the specific files approved by the control window. The approval must name exact paths — glob patterns are not sufficient.

**Done condition**: approval documented, only approved files touched, all `artifact_outputs` exist and parse, `make check` passes, approval reference in commit message.

---

## Relationship to ADRs

| DoD section | ADR |
|-------------|-----|
| Required artifacts | ADR-0006 (artifact bundle) |
| Rollback semantics | ADR-0003 (workspace contract — `failed` state) |
| Telemetry completeness | ADR-0001 (session schema — `stop_reason`, `real_paths_rerun`) |
| Escalation handling | ADR-0005 (permission model — escalation triggers) |
| Acceptance rules | ADR-0004 (inference gateway — LOCAL-FIRST routing) |
| Autonomy scorecard | ADR-0007 (governance_conformance dimension) |

---

## Example

See `governance/execution_control_package.example.json` for an example package whose `validation_order`, `rollback_rule`, and `artifact_outputs` conform to this Definition of Done.
