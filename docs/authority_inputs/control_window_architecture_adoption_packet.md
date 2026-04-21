# Control Window Architecture Adoption Packet
## Authority Reference: Phase 0 — Governance Source-of-Truth Reconciliation

**Document type**: architecture_adoption_packet  
**Authority scope**: Phase 0 authority surface reconciliation  
**Version**: 1.0  
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
- **Gap identified**: Phase 0 (`governance_source_of_truth_reconciliation`) has no closure record despite phases 2–7 being ratified.

### AS-CW-03 — next_package_class is the Gating Surface for Package Admission
- **Path**: `governance/next_package_class.json`
- **Authority claim**: The `current_allowed_class` field in `next_package_class.json` is the binding gate for all package admissions. Packages of a non-allowed class must be rejected by the execution terminal.

### AS-CW-04 — runtime_contract_version Governs Phase 1 Closure
- **Path**: `governance/runtime_contract_version.json`
- **Authority claim**: Phase 1 (`runtime_contract_foundation`) may not close until `runtime_contract_version.json` is explicitly ratified by a governance ADR. The contract_version fingerprint must be re-verified at closure time.

## Adoption Order

1. Ratify Phase 0 closure with a formal `phase0_closure_decision.json` and ADR.
2. Reconcile `current_phase.json` to reflect Phase 0 closed.
3. Update `phase_gate_status.json` Phase 0 entry from `open` to `closed_ratified`.
4. Proceed to Phase 1 hardening with runtime_contract_version ratification.

## Conflicts Acknowledged

- `current_phase.json` is stale: reports `current_phase_id=0` (open) while `next_package_class.json` reflects Phase 7 closure (`ratification_only`).
- `config/promotion_manifest.json` migration is deferred pending explicit authority.
