# Execution Control Package Specification

**Spec ID**: EXEC-CTRL-PKG-SPEC-1  
**Status**: active  
**Date**: 2026-04-21  
**Phase linkage**: Phase 0 (governance_source_of_truth_reconciliation), Phase 1 (runtime_contract_foundation)  
**Authority sources**: ADR-0001, ADR-0003, ADR-0006, ADR-0007, P0-01-AUTHORITY-SURFACE-INVENTORY-1, governance/execution_control_package.schema.json

---

## Purpose

An **execution control package** is the machine-readable contract governing a single bounded coding slice in the integrated AI platform. Every SUBSTRATE and LOCAL-FIRST session operates under an explicit package that declares what it may touch, how it must validate its work, when it must escalate, and what it must produce.

This specification defines the structure, semantics, and governance constraints of execution control packages.

---

## Structure

An execution control package is a JSON object conforming to `governance/execution_control_package.schema.json`. Every package must include the following fields:

### `package_id`

Unique stable identifier. Format: `{COMPONENT}-P{phase}-{DESCRIPTOR}-{sequence}`

Examples:
- `P0-01-AUTHORITY-SURFACE-INVENTORY-1`
- `P0-02-CORE-ADR-SET-1`
- `LACE2-P9-REAL-FILE-RUNNER-SEAM-1`

The `package_id` is immutable after issuance. Recovery attempts must use the same `package_id` with a recovery note.

### `label`

Execution routing label. Must be one of:
- `SUBSTRATE` — Claude Code implements directly
- `LOCAL-FIRST` — must route to Aider/Ollama exec terminal
- `ESCALATION` — requires control window approval before proceeding

### `objective`

Single focused goal for this package. Must not be compound or speculative. The objective is the primary reference for scope compliance verification.

### `allowed_files`

Exhaustive list of file paths this package may create or modify. Paths may include glob patterns. Any file touched that is not in this list is a scope violation and triggers rollback.

### `forbidden_files`

Exhaustive list of file paths or patterns this package must not touch under any circumstances. Takes precedence over `allowed_files` in case of conflict.

**Default forbidden categories** (apply to all packages unless explicitly overridden by ESCALATION label):
- `framework/**` — all existing framework modules
- `governance/canonical_roadmap.json` — immutable without closure ADR
- `governance/authority_adr_*` — append-only
- `config/promotion_manifest.json` — frozen pending migration

### `validation_order`

Ordered sequence of validation steps. Each step must pass before the next begins. Steps are numbered from 1. A step may specify:
- `description` — human-readable description
- `command` — shell command to execute
- `check` — file/artifact existence or parse check

### `rollback_rule`

What to do if any gate fails:
- `remove_on_failure` — files created by this package that must be deleted
- `preserve_always` — pre-existing files that must never be modified or removed

The rollback rule is executed by the exec terminal on any hard stop or gate failure.

### `artifact_outputs`

Required artifact files this package must produce. Each entry specifies:
- `path` — relative path from repo root (under `artifacts/` or `governance/`)
- `artifact_id` — stable identifier embedded in the artifact
- `required_fields` — JSON fields that must be present in the artifact

### `escalation_rule`

Conditions under which this package must escalate:
- `escalate_if` — list of trigger conditions (e.g., "any forbidden file would need to be modified", "scope exceeds 5 files")
- `escalation_route` — where escalation is directed (`control_window`, `human_review`)

### `acceptance_gates`

All conditions that the control window checks before accepting the package. Every gate must be explicitly satisfied. The acceptance gate list is exhaustive — unlisted conditions are not evaluated.

### `phase_linkage`

Canonical phase(s) this package operates under, referencing `governance/canonical_roadmap.json` phase IDs.

### `authority_sources`

Governance authority surfaces that constrain this package, e.g., ADR IDs, P0-01 surface IDs, governance file paths.

### `schema_version`

Integer version of the execution control package schema. Current: `1`.

---

## Package Lifecycle

```
issued → active → [executing | escalated] → [completed | rolled_back]
```

1. **issued** — control window issues package to exec terminal
2. **active** — exec terminal begins validation and implementation
3. **executing** — implementation in progress (files being created/modified)
4. **escalated** — exec terminal hit a hard stop; escalating to control window
5. **completed** — all acceptance gates satisfied; commit produced
6. **rolled_back** — one or more gates failed; package files removed

---

## Scope Compliance Rule

A package is scope-compliant if and only if:
1. Every file touched is in `allowed_files`
2. No file in `forbidden_files` was modified
3. No file outside `allowed_files` was created
4. All `artifact_outputs` were produced at their declared paths

Scope violations are hard stops. The exec terminal must report the violation explicitly and execute the rollback rule before reporting failure.

---

## Recovery Protocol

If a package is rejected by the control window:
1. Keep the same `package_id`
2. Fix the specific failure identified in the rejection
3. Re-run full validation order from step 1
4. Commit with recovery note: `{package_id} (recovered): {one-line fix description}`

---

## Relationship to ADRs

Execution control packages are governed by:
- **ADR-0001** (canonical session/job schema) — package execution occurs within a `governance_session`
- **ADR-0003** (workspace contract) — `allowed_files` maps to workspace `allowed_write_paths`; `forbidden_files` maps to `forbidden_write_paths`
- **ADR-0006** (artifact bundle) — `artifact_outputs` must appear in the session's artifact bundle with `artifact_type=governance`
- **ADR-0007** (autonomy scorecard) — package outcomes are recorded in the `escalation_rate` and `governance_conformance` dimensions

---

## Example

See `governance/execution_control_package.example.json` for a complete valid package that conforms to this specification and the JSON schema at `governance/execution_control_package.schema.json`.
