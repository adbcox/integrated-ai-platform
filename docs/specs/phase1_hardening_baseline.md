# Phase 1 Hardening Baseline Specification

**Spec ID**: PHASE1-HARDENING-BASELINE-SPEC-1  
**Status**: active  
**Date**: 2026-04-21  
**Phase linkage**: Phase 1 (runtime_contract_foundation)  
**Authority sources**: governance/canonical_roadmap.json (Phase 1 definition), governance/definition_of_done.v1.yaml, governance/cmdb_lite_registry.v1.yaml

---

## Purpose

This document specifies the Phase 1 hardening baseline — the completion criteria and substrate authority lock for Phase 1 of the integrated AI platform. Phase 1 is declared materially locked when all required governance contracts exist, have passing seam tests, and are cross-referenced in the machine-readable baseline file.

The machine-readable form is `governance/phase1_hardening_baseline.v1.yaml`. This document is the human-readable companion.

---

## Phase Identity

- **Phase ID**: `phase_1`
- **Label**: Phase 1 — Runtime Contract Foundation
- **Status**: `substrate_authority_locked`
- **Scope**: Governance and substrate contract work only; no runtime implementation

---

## Objective

Phase 1 must create and ratify the complete set of governance contracts governing:
- How coding runs execute (workspace contract, wrapped command contract)
- What they may write (artifact root contract)
- How results are normalized (telemetry normalization contract)
- How validation is sequenced (local run validation pack)
- What models they may use (model profiles, inference gateway contract)

Phase 1 ends when these contracts exist, are validated, and are cross-referenced here. Runtime implementation of these contracts is Phase 2 work.

---

## Required Contracts

All seven contracts must exist as machine-readable YAML with companion spec documents:

| Contract | YAML path | Spec path | Package |
|----------|-----------|-----------|---------|
| Model profiles | `governance/model_profiles.v1.yaml` | `docs/specs/model_profiles.md` | P1-01 |
| Inference gateway | `governance/inference_gateway_contract.v1.yaml` | `docs/specs/inference_gateway_contract.md` | P1-02 |
| Workspace contract | `governance/workspace_contract.v1.yaml` | `docs/specs/workspace_contract.md` | P1-03 |
| Wrapped command | `governance/wrapped_command_contract.v1.yaml` | `docs/specs/wrapped_command_contract.md` | P1-05 |
| Artifact root | `governance/artifact_root_contract.v1.yaml` | `docs/specs/artifact_root_contract.md` | P1-06 |
| Telemetry normalization | `governance/telemetry_normalization_contract.v1.yaml` | `docs/specs/telemetry_normalization_contract.md` | P1-06 |
| Local run validation pack | `governance/local_run_validation_pack.v1.yaml` | `docs/specs/local_run_validation_pack.md` | P1-06 |

---

## Completion Requirements

Phase 1 is complete when all four conditions are simultaneously true:

### 1. Reproducible local runs

A coding run can execute locally without manual environment repair. Evidence: passing seam tests for all Phase 1 contract packages.

**Status: met.**

### 2. Complete artifacts

All governance artifacts declared in `required_contracts[*].artifact_path` exist, parse as valid JSON, and contain all required fields.

**Status: met.**

### 3. No manual environment repair

No Phase 1 package required manual intervention to fix a missing dependency, missing file, or environment state not captured in grounding inputs. Any exceptions documented in `residual_notes`.

**Status: met.**

### 4. Explicit escalation accounting

Every Phase 1 package explicitly reports `escalation_status`. All packages in this phase report `NOT_ESCALATED`. Escalation count: 0.

**Status: met.**

---

## Blockers

**Unresolved blockers**: none.

**Resolved blockers**:
- **P1-BLOCKER-01**: Phase 1 contracts did not exist at session start. Resolved by packages P1-01 through P1-06 in the exec-lane execution lane.

---

## Notes

### Phase 2 scope

Phase 2 (local runtime implementation) picks up where Phase 1 leaves off:
- Implement `framework/wrapped_command_runner.py`
- Wire the telemetry emission pipeline
- Integrate the inference gateway contract into `framework/inference_adapter.py`
- Execute the local run validation pack sequence automatically at package end

### P1-04 slot

Package P1-04 was not issued in this execution lane. The sequence ran P1-01 → P1-02 → P1-03 → P1-05 → P1-06. The P1-04 slot is reserved for a future permission model contract if the control window issues it.

### Authority lock meaning

`substrate_authority_locked` means the contracts in `required_contracts` are the authoritative definitions for Phase 1 execution semantics. They may be amended by subsequent packages with explicit `allowed_files` declarations, but they may not be silently replaced or overwritten.

### Exec lane commit sequence

Packages executed on `exec-lane` branch:
P0-02, P0-03, P0-04, P0-05, P0-06, P1-01, P1-02, P1-03, P1-05, P1-06

---

## Relationship to ADRs and Governance

| Baseline element | Authority |
|-----------------|-----------|
| Phase completion | governance/canonical_roadmap.json Phase 1 definition |
| Required contracts | governance/cmdb_lite_registry.v1.yaml runtime_contract |
| Completion requirements | governance/definition_of_done.v1.yaml |
| Escalation accounting | governance/autonomy_scorecard.v1.yaml |
