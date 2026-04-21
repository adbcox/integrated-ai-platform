# Phase 2 Substrate Baseline Specification

**Spec ID**: PHASE2-SUBSTRATE-BASELINE-SPEC-1  
**Status**: active  
**Date**: 2026-04-21  
**Phase linkage**: Phase 2 (minimum_substrate_implementation)  
**Authority sources**: governance/phase1_hardening_baseline.v1.yaml, governance/local_run_validation_pack.v1.yaml, governance/definition_of_done.v1.yaml

---

## Purpose

This document specifies the Phase 2 substrate baseline — the minimum implementation surface that must exist before Phase 3 (live runtime integration) can begin. Phase 2 produces a small, coherent, standalone set of substrate modules that prove the Phase 1 governance contracts can be instantiated and tested without modifying existing dense framework modules.

The machine-readable form is `governance/phase2_substrate_baseline.v1.yaml`. This document is the human-readable companion.

---

## Phase Identity

- **Phase ID**: `phase_2`
- **Label**: Phase 2 — Minimum Substrate Implementation
- **Status**: `in_progress` (gate met by P2-02)
- **Scope**: New-file implementation only; no modifications to existing live runtime modules

---

## Required Modules

Twelve modules must exist across two packages:

### From P2-01

| Module | Classes |
|--------|---------|
| `framework/session_job_schema_v1.py` | `SessionRecord`, `JobRecord` |
| `framework/tool_contracts_v1.py` | `ToolContractV1` (+ 4 instances) |
| `framework/tool_registry_v1.py` | `ToolRegistryV1` |
| `framework/workspace_controller_v1.py` | `WorkspaceDescriptorV1`, `WorkspaceControllerV1` |
| `framework/permission_decision_v1.py` | `PermissionDecisionV1`, `Decision` |
| `framework/artifact_bundle_v1.py` | `ArtifactBundleV1` |

### From P2-02

| Module | Classes |
|--------|---------|
| `framework/read_file_tool_v1.py` | `ReadFileToolV1`, `ReadFileResultV1` |
| `framework/publish_artifact_tool_v1.py` | `PublishArtifactToolV1`, `PublishArtifactResultV1` |
| `framework/run_command_tool_v1.py` | `RunCommandToolV1`, `RunCommandResultV1` |
| `framework/run_tests_tool_v1.py` | `RunTestsToolV1`, `RunTestsResultV1` |
| `framework/substrate_runtime_v1.py` | `SubstrateRuntimeV1` |
| `framework/substrate_conformance_v1.py` | `SubstrateConformanceCheckerV1`, `ConformanceResultV1` |

---

## Required Tools

Four tool implementations must be present and registered in `ToolRegistryV1`:

| Tool | Class | Side-effecting |
|------|-------|----------------|
| `read_file` | `ReadFileToolV1` | No |
| `publish_artifact` | `PublishArtifactToolV1` | Yes |
| `run_command` | `RunCommandToolV1` | Yes |
| `run_tests` | `RunTestsToolV1` | No |

---

## Conformance Requirements

The `SubstrateConformanceCheckerV1` verifies six requirements:

| Requirement | Verified by |
|------------|-------------|
| `tool_registry_complete` | `ToolRegistryV1()` contains all 4 tools |
| `workspace_validates` | `WorkspaceControllerV1.validate_layout()` returns True |
| `artifact_bundle_assembles` | `ArtifactBundleV1.to_dict()` succeeds |
| `substrate_artifact_emitted` | `PublishArtifactToolV1.run()` is callable |
| `read_file_reads_real_file` | `ReadFileToolV1.run()` returns `status='success'` |
| `publish_artifact_writes_file` | `PublishArtifactToolV1.run()` returns `bytes_written > 0` |

---

## Completion Gate

Phase 2 substrate is complete when:
1. All conformance requirements are met
2. The substrate can execute a complete end-to-end flow: read a file → make a permission decision → run a command → publish an artifact
3. Seam tests pass
4. `make check` passes

**Gate status**: Met by P2-01 + P2-02.

---

## Remaining Blockers

### P2-BLOCKER-01 (deferred to Phase 3)

`SubstrateRuntimeV1` is not yet wired into existing live runtime modules. `framework/inference_adapter.py`, `framework/code_executor.py`, and related production modules do not yet use the v1 substrate surfaces.

**Resolution path**: Phase 3 integration packages will wire the v1 substrate into production modules incrementally.

### P2-BLOCKER-02 (deferred to Phase 3)

Structured telemetry emission (per `telemetry_normalization_contract.v1.yaml`) is not yet implemented in the tool implementations. `run_command_tool_v1` and `run_tests_tool_v1` do not yet emit structured events.

**Resolution path**: A Phase 3 package will add event emission following the telemetry normalization contract.

---

## Relationship to Governance

| Baseline element | Authority |
|-----------------|-----------|
| Required modules | governance/phase1_hardening_baseline.v1.yaml (Phase 2 scope) |
| Conformance requirements | governance/local_run_validation_pack.v1.yaml |
| Tool contracts | governance/wrapped_command_contract.v1.yaml |
| Artifact emission | governance/artifact_root_contract.v1.yaml |
| Remaining blockers | governance/definition_of_done.v1.yaml (acceptance gates) |
