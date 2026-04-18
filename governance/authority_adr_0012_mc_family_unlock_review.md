# ADR 0012 — MC Family Tactical Unlock Review (first-pass, remains_locked)

Status: accepted (TREV-MC-1)
Owner: governance/mc_family_unlock_review.json
Baseline commits:
- RECON-W1: 53ae4d4f177b176a7bffaa63988f63fa0efa622c
- RECON-W2A: 595dc8750ed671fb23d3cec0be434c76dad818f5
- RECON-W2C: 6b2446180a4d1e9194ef682aacd33fc12f1f4c46
- TREV-EO-1 baseline: ae4077bc8b48b445e6e783e772e6ccc58c53b525
- TREV-ED-1 baseline: 9c2420736e9542596b0d37c581cef3cba7fd2402
- TREV-MC-1 baseline: 9c2420736e9542596b0d37c581cef3cba7fd2402

## Context

governance/tactical_unlock_criteria.json records MC as locked and
review_packet_required = true.
governance/authority_adr_0006_tactical_unlock_criteria.md requires a
per-family review packet before any family can move out of locked. This
ADR is the first MC-only review. This ADR does not evaluate or modify
any other family.

MC is a distinctive case among tactical families: a substantial evidence
surface exists under `framework/multi_phase_*` (271 helper files at this
baseline per runtime_adoption_report.json), but that surface has not
been wired to the shared runtime primitives, and the canonical phase
that gates MC work (Phase 4) is not authorized.

## Decision

MC remains_locked.

At baseline commit 9c2420736e9542596b0d37c581cef3cba7fd2402:

1. Canonical Phase 4 authority does not permit MC work.
   governance/canonical_roadmap.json records Phase 4
   (autonomy_hardening_safety_policy_uplift) as status = open and
   "not canonically authorized until Phase 2/3 governance closure."
   MC has canonical_phase_dependency = 4 per
   governance/tactical_family_classification.json, so MC advancement is
   not admissible at this baseline.
2. runtime_adoption_report.json records adopting_files = 0 and
   adopting_paths = [] for MC. Despite 271 committed
   framework/multi_phase_* helpers, none of them statically import any
   framework runtime primitive (worker_runtime, tool_system, workspace,
   permission_engine, sandbox). Adoption is unmeasured.
3. No named offline regression scenario covers multi-phase autonomy.
   No tests/test_mc_.py file exists and no multi-phase-autonomy case
   exists in tests/run_offline_scenarios.sh.

Zero of three preconditions are met. Under conservative tactical-review
policy, MC cannot advance to eligible_for_review or unlocked at this
baseline.

This packet is governance-only and read-only. It does not consume a
class transition, does not generate MC code, does not modify the
framework/multi_phase_* surface, and does not modify
tactical_unlock_criteria.json.

## Consequences

- governance/tactical_unlock_criteria.json is unchanged.
- governance/tactical_family_classification.json is unchanged.
- No mc_ or multi_phase_ code is created.
- No mc_* regression fixture is created.
- next_package_class.json#current_allowed_class remains "ratification_only".

## Invariants explicitly preserved

- No other family is evaluated or changed.
- LOB-W3 remains paused under
  governance/authority_adr_0003_lob_w3_classification.md.
- Canonical phases remain 0..6.
- Phase 4 remains open and unadvanced.
- No framework/ byte changes.
- No bin/ byte changes.
- No existing ADR byte changes.
- No generator source byte changes.
- Living generator-owned artifacts classified by
  governance/authority_adr_0009_living_generator_artifacts.md remain
  unchanged because this packet adds no new framework primitive consumers.

## Next review

A later TREV-MC-2 packet may be opened only after separate non-review
packets commit all of the following:
- canonical Phase 4 advanced to closed_ratified (or otherwise explicitly
  authorized to admit MC work) via a separate non-review packet,
- at least one framework/multi_phase_*.py or framework/mc_*.py file with
  a real static import of a Phase-1 runtime primitive such that
  runtime_adoption_report.json tactical_family_adoption for mc shows
  adopting_files >= 1, and
- at least one tests/test_mc_.py regression scenario wired into
  tests/run_offline_scenarios.sh covering multi-phase autonomy.

This ADR does not authorize any of that follow-on work.

## Supersedes

None.
