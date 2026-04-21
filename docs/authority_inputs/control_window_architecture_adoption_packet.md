# Control Window Architecture Adoption Packet
## Authority Reference: Phase 0 — Governance Source-of-Truth Reconciliation

**Document type**: architecture_adoption_packet  
**Authority scope**: Phase 0 authority surface reconciliation  
**Version**: 1.1  
**Status**: active

---

## Authority Surfaces Declared

This adoption packet declares the following as canonical authority surfaces for the integrated AI platform:

### AS-CW-01 — Governance Directory as Single Source of Truth
- **Path**: `governance/`
- **Authority claim**: All machine-readable governance artifacts in `governance/` supersede narrative documents in `docs/` and legacy manifests in `config/`.
- **Ratified by**: `governance/authority_adr_0001_source_of_truth.md`

### AS-CW-02 — Phase Closure Requires Explicit Record
- **Path**: `governance/phase_gate_status.json`, closure decision files
- **Authority claim**: No phase may be considered closed without a `phase{N}_closure_decision.json` artifact and a corresponding ADR. Procedural bypass is not permitted.

### AS-CW-03 — next_package_class is the Gating Surface for Package Admission
- **Path**: `governance/next_package_class.json`
- **Authority claim**: The `current_allowed_class` field in `next_package_class.json` is the binding gate for all package admissions.

### AS-CW-04 — runtime_contract_version Governs Phase 1 Closure
- **Path**: `governance/runtime_contract_version.json`
- **Authority claim**: Phase 1 may not close until runtime contract is explicitly ratified.

### AS-CW-05 — Local Autonomy and Adapter Boundary Architecture (RM-DEV-005)
- **Authority claim**: The system architecture is now formally **local-first with governed adapters**.
- **Key constraints (ratified)**:
  - Aider is a **controlled adapter / transport target only**, not a backbone
  - No permanent direct coupling between Aider and core runtime or Ollama
  - OSS components must sit behind repo-owned wrapper boundaries
- **Authority sources**:
  - `governance/authority_adr_0023_rm_dev_005a_adapter_boundary.md`
  - `governance/rm_dev_005a_authority_state.v1.yaml`
  - `governance/oss_intake_registry.v1.yaml`
- **Validation backing**:
  - `artifacts/substrate/phase4_uplift_pack_check.json`
  - `artifacts/substrate/phase5_closeout_pack_check.json`
  - `artifacts/governance/rm_dev_005a_authority_validation.json`
- **Architecture implication**:
  - Ollama-first inference remains default
  - All execution adapters (including Aider) are removable and non-authoritative
  - Local autonomy must be justified by artifact evidence, not qualitative claims

## Adoption Order

1. Ratify Phase 0 closure
2. Reconcile phase state
3. Enforce package gating
4. Maintain runtime contract discipline
5. Operate under RM-DEV-005 local-first + adapter-governed architecture

## Conflicts Acknowledged

- Historical drift between phase state and runtime gating surfaces has been resolved via repo-visible authority artifacts.
