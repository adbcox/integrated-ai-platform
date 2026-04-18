# ADR 0016 — MC Review Amendment for Seed Compatibility

Status: accepted (TREV-MC-1-AMEND)
Owner: governance/mc_family_unlock_review.json
Baseline commits:
- RECON-W1:   53ae4d4f177b176a7bffaa63988f63fa0efa622c
- RECON-W2A:  595dc8750ed671fb23d3cec0be434c76dad818f5
- RECON-W2C:  6b2446180a4d1e9194ef682aacd33fc12f1f4c46
- TREV-MC-1:  3b7278b533ed9f5ea726c75a721f09cec0e959ba

## Context

TREV-MC-1 correctly concluded that MC remained_locked at its review
baseline because:
1. canonical phase authority for MC remained unmet,
2. MC runtime adoption was zero at that baseline,
3. no named offline regression scenario existed.

A later additive seed packet is expected to introduce runtime adoption
and a named regression scenario without unlocking MC. The original
enforcement test encoded zero adoption as a perpetual invariant, which
blocks that legitimate future seed work even though ADR 0006 requires
all preconditions, including canonical phase authority, before any
unlock review can advance MC.

## Decision

1. TREV-MC-1 remains substantively correct and remains in force:
   - MC remains_locked
   - MC classification remains provisional_precursor
   - current_allowed_class remains ratification_only
   - no tactical family unlock is authorized

2. The MC review artifact and its test are amended to be baseline-scoped
   rather than future-eternal:
   - runtime adoption for MC may increase in a later additive packet
     without invalidating the TREV-MC-1 remains_locked decision
   - a named offline regression scenario for MC may be added in a later
     additive packet without invalidating the TREV-MC-1 remains_locked
     decision
   - canonical phase authority remains the gating precondition that
     still must be unmet until a later TREV-MC review reevaluates MC

3. This ADR does not unlock MC, does not authorize TREV-MC-2, and does
   not modify tactical_unlock_criteria.json. It only removes an
   internal contradiction that prevented future seed work from
   coexisting with the still-locked MC family state.

## Consequences

- Future additive MC seed packets may introduce:
  - a real MC runtime adopter
  - a named offline regression scenario
  without requiring tactical_unlock_criteria.json or
  tactical_family_classification.json to change.

- A later TREV-MC-2 packet must still reevaluate MC mechanically
  against all three preconditions.
- Unless canonical phase authority is also satisfied, MC remains_locked.

## Supersedes

- The zero-adoption-forever interpretation implicit in
  tests/test_governance_mc_family_unlock_review.py as committed by
  TREV-MC-1.
