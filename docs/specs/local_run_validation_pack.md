# Local Run Validation Pack Specification

**Spec ID**: LOCAL-RUN-VALIDATION-PACK-SPEC-1  
**Status**: active  
**Date**: 2026-04-21  
**Phase linkage**: Phase 1 (runtime_contract_foundation)  
**Authority sources**: governance/definition_of_done.v1.yaml, governance/execution_control_package.schema.json

---

## Purpose

This document specifies the local run validation pack for all coding runs in the integrated AI platform. The **validation pack** defines the ordered sequence of checks that every package execution must pass before its outputs are accepted and committed. It specifies what each check must verify, how failures are handled, and how requirements differ by package class (SUBSTRATE / LOCAL-FIRST / ESCALATION).

The machine-readable form is `governance/local_run_validation_pack.v1.yaml`. This document is the human-readable companion.

---

## The No-Skip Rule

> **A package cannot be accepted without passing the full validation sequence.**

Claiming completion without validation evidence is a DoD violation. Every gate in the sequence is blocking. A failed gate stops execution and triggers rollback of the current package's files only.

---

## Validation Sequence

Six steps, executed in order:

| Step | Name | Command | Blocking |
|------|------|---------|----------|
| 1 | `grounding_check` | Embedded in runner | Yes |
| 2 | `import_check` | `python3 -c 'import <runner>'` | Yes |
| 3 | `package_runner` | `python3 bin/run_<slug>.py` | Yes |
| 4 | `emitted_artifact_parse` | `python3 -m json.tool <artifact>` | Yes |
| 5 | `package_seam_tests` | `python3 -m pytest tests/test_<slug>_seam.py -v` | Yes |
| 6 | `make_check` | `make check` | Yes |

Steps must be executed in order. Skipping a step requires `skip_condition` documentation in the package's `validation_order`.

### Step 1: Grounding Check

Verifies all declared grounding inputs exist and are non-empty (size > 50 bytes). A missing or empty grounding input is a hard stop — grounding is a prerequisite for all subsequent validation.

### Step 2: Import Check

Verifies the runner module imports without error and all required callables are present (`_load_yaml`, `_check_content`, etc.). A module import failure indicates a broken runner — no further steps can proceed.

### Step 3: Package Runner

Executes the runner script and verifies exit code 0. The runner script is the canonical authority on whether the contract/artifact is valid. A non-zero exit stops the sequence.

### Step 4: Emitted Artifact Parse

Verifies the artifact exists at its declared path, parses as valid JSON, and contains all required fields including `artifact_id`, `yaml_loaded`, and `required_sections_present`. A malformed artifact means the runner succeeded but produced invalid output.

### Step 5: Package Seam Tests

Runs the complete seam test suite. All tests must pass — no failures, no errors. Critical seam tests that must pass: `test_runner_script_executes`, `test_content_check_passes`, `test_emit_artifact`.

### Step 6: make check

Runs the full repository syntax check (`make check`). Covers shell script syntax validation and Python syntax for all top-level Python files. A failing `make check` blocks commit.

---

## Required Checks per Step

### Grounding check must verify
- All grounding input files exist
- All grounding input files have `st_size > 50` bytes

### Import check must verify
- Runner module imports without `ImportError`
- All required callables present

### Package runner must verify
- Runner exits with code 0
- Runner prints confirmation of required sections and fields
- Artifact path printed to stdout

### Emitted artifact parse must verify
- Artifact file exists at declared path
- Artifact parses as valid JSON
- `artifact_id` field matches expected value
- All required artifact fields present

### Package seam tests must verify
- All collected tests pass (0 failures, 0 errors)
- `test_runner_script_executes` passes
- `test_content_check_passes` passes
- `test_emit_artifact` passes

### make check must verify
- Shell script syntax check passes
- Python syntax check passes

---

## Artifact Requirements

Every accepted package must emit a governance artifact containing:

**Minimum required fields** (all packages):
- `artifact_id`, `generated_at`, `phase_linkage`, `authority_sources`

**Additional required fields** (contract packages):
- `contract_path`, `yaml_loaded`, `required_sections_checked`, `required_sections_present`

`generated_at` must be an ISO 8601 timestamp with timezone — plain date strings are not permitted.

---

## Failure Handling

| Failure mode | Action |
|-------------|--------|
| `stop_on_failed_gate` | Immediately stop execution; do not proceed past failed gate |
| `no_accept_without_validation` | Package cannot be accepted without full validation evidence |
| `slice_only_rollback` | Rollback scoped to current package files only; never touch pre-existing files |
| Partial artifacts | Remain in artifact root; listed in `hard_stops_hit` and `residual_notes` |

**Rollback scoping**: On gate failure, `rollback_rule.remove_on_failure` applies only to files the current package created. Pre-existing files are inviolable (`preserve_unrelated_changes = true`).

---

## Package Class Rules

| Class | Executor | Inference | Local model required | Escalation accounting |
|-------|---------|-----------|---------------------|----------------------|
| SUBSTRATE | Claude Code | No | No | `escalation_status` required |
| LOCAL-FIRST | Aider / Ollama | Yes | Yes (claude rescue = escalation) | `escalation_status` required |
| ESCALATION | Manual / escalation-routed | No | No | `escalation_status = ESCALATED` required |

### LOCAL-FIRST: claude rescue counts as escalation

If a LOCAL-FIRST package is executed by Claude Code instead of a local model (claude rescue), `escalation_status` must be `ESCALATED` in telemetry. Passing all gates via claude rescue does not count as local autonomy progress.

All validation gates (seam tests, make check) still apply regardless of package class.

---

## Exceptions

### Documentation-only packages skip import/runner steps

Packages producing only ADR or spec files without a runner script may declare `no_runner=true` to skip steps 2 and 3. All other steps apply.

### Seam test reuse for contract updates

A package updating an existing contract may extend the existing seam test file (with new test functions) rather than creating a new file, provided the existing file is in `allowed_files`.

### Known pre-existing `make check` failures

If `make check` fails due to a pre-existing known failure in an unrelated module, the package may proceed with that failure flagged in `residual_notes`. The package-specific files must still pass.

### Phase 2 defers full telemetry emission

Phase 1 packages are not required to emit structured telemetry event streams. Artifact fields constitute the Phase 1 telemetry record. Full event stream emission is deferred to Phase 2.

---

## Relationship to ADRs and Governance

| Contract element | Authority |
|-----------------|-----------|
| Validation sequence | governance/definition_of_done.v1.yaml `required_validation` |
| Failure handling | ADR-0003 (workspace contract — `cleanup_policy`) |
| Slice-only rollback | workspace_contract.v1.yaml `preserve_unrelated_changes` |
| Package class rules | governance/definition_of_done.v1.yaml `acceptance_rules` |
| Claude rescue rule | governance/definition_of_done.v1.yaml `acceptance_rules.local_first` |
