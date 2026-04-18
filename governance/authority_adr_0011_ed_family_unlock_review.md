# ADR 0011 — ED Family Tactical Unlock Review (first-pass, remains_locked)

Status: accepted (TREV-ED-1)
Owner: governance/ed_family_unlock_review.json
Baseline commits:
- RECON-W1: 53ae4d4f177b176a7bffaa63988f63fa0efa622c
- RECON-W2A: 595dc8750ed671fb23d3cec0be434c76dad818f5
- RECON-W2C: 6b2446180a4d1e9194ef682aacd33fc12f1f4c46
- TREV-ED-1 baseline: ae4077bc8b48b445e6e783e772e6ccc58c53b525

## Context

governance/tactical_unlock_criteria.json records ED as locked and
review_packet_required = true.
governance/authority_adr_0006_tactical_unlock_criteria.md requires a
per-family review packet before any family can move out of locked. This
ADR is the first ED-only review. This ADR does not evaluate or modify any
other family.

## Decision

ED remains_locked.

At baseline commit ae4077bc8b48b445e6e783e772e6ccc58c53b525:

1. No reviewable ED code surface exists under framework/. No
   framework/ed_.py file exists. ED is classified provisional_precursor
   with canonical_phase_dependency = 2; although Phase 2 is
   closed_ratified, no ED code surface has been committed for review.
2. runtime_adoption_report.json records adopting_files = 0 and
   adopting_paths = [] for ED. No ed_-prefixed consumer exists in
   governance/schema_contract_registry.json.
3. No named offline regression scenario covers ED. No tests/test_ed_.py
   file exists and no ED case exists in tests/run_offline_scenarios.sh.

Zero of three preconditions are met. Under conservative tactical-review
policy, ED cannot advance to eligible_for_review or unlocked at this
baseline.

This packet is governance-only and read-only. It does not consume a class
transition, does not generate ED code, and does not modify
tactical_unlock_criteria.json.

## Consequences

- governance/tactical_unlock_criteria.json is unchanged.
- governance/tactical_family_classification.json is unchanged.
- No ed_ code is created.
- No ed_* regression fixture is created.
- next_package_class.json#current_allowed_class remains "ratification_only".

## Invariants explicitly preserved

- No other family is evaluated or changed.
- LOB-W3 remains paused under
  governance/authority_adr_0003_lob_w3_classification.md.
- Canonical phases remain 0..6.
- No framework/ byte changes.
- No bin/ byte changes.
- No existing ADR byte changes.
- No generator source byte changes.
- Living generator-owned artifacts classified by
  governance/authority_adr_0009_living_generator_artifacts.md remain
  unchanged because this packet adds no new framework primitive consumers.

## Next review

A later TREV-ED-2 packet may be opened only after a separate non-review
packet commits:
- at least one framework/ed_.py file with a real static import of a
  Phase-1 runtime primitive, and
- at least one tests/test_ed_.py regression scenario wired into
  tests/run_offline_scenarios.sh.

This ADR does not authorize that follow-on work.

## Supersedes

None.
