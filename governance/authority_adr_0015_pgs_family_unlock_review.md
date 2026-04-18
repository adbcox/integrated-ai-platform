# ADR 0015 — PGS Family Tactical Unlock Review (first-pass, remains_locked)

Status: accepted (TREV-PGS-1)
Owner: governance/pgs_family_unlock_review.json
Baseline commits:
- RECON-W1: 53ae4d4f177b176a7bffaa63988f63fa0efa622c
- RECON-W2A: 595dc8750ed671fb23d3cec0be434c76dad818f5
- RECON-W2C: 6b2446180a4d1e9194ef682aacd33fc12f1f4c46
- TREV-EO-1 baseline: ae4077bc8b48b445e6e783e772e6ccc58c53b525
- TREV-ED-1 baseline: 9c2420736e9542596b0d37c581cef3cba7fd2402
- TREV-MC-1 baseline: 9c2420736e9542596b0d37c581cef3cba7fd2402
- TREV-LIVE_BRIDGE-1 baseline: 3b7278b533ed9f5ea726c75a721f09cec0e959ba
- TREV-ORT-1 baseline: 2d51712ae6e0015a8fbb5faed3da08004267ada6
- TREV-PGS-1 baseline: d8addca14c9a6b76e1a4e0cf1b45ef1e31e470f8

## Context

governance/tactical_unlock_criteria.json records PGS as locked and
review_packet_required = true.
governance/authority_adr_0006_tactical_unlock_criteria.md requires a
per-family review packet before any family can move out of locked.
This ADR is the first PGS-only review. This ADR does not evaluate or
modify any other family.

PGS has the largest committed evidence surface of any tactical family
(1500 helper files under `framework/pgs_*` at this baseline per
runtime_adoption_report.json), but that surface has not been wired to
the shared runtime primitives and the canonical phase that gates PGS
work (Phase 5) is `open`. This review records those facts and declines
to advance PGS.

## Decision

PGS remains_locked.

At baseline commit d8addca14c9a6b76e1a4e0cf1b45ef1e31e470f8:

1. Canonical Phase 5 authority does not permit PGS work.
   governance/canonical_roadmap.json records Phase 5
   (qualification_promotion_learning_convergence) as status = open and
   "not canonically authorized until Phase 4 closure". PGS has
   canonical_phase_dependency = 5 per
   governance/tactical_family_classification.json, so PGS advancement
   is not admissible at this baseline.
2. runtime_adoption_report.json records adopting_files = 0 and
   adopting_paths = [] for PGS. Despite 1500 committed
   framework/pgs_* helpers, none of them statically import any
   framework runtime primitive (worker_runtime, tool_system, workspace,
   permission_engine, sandbox). Adoption is unmeasured.
3. No named offline regression scenario covers PGS governance helpers.
   No tests/test_pgs_*.py file exists and no PGS case exists in
   tests/run_offline_scenarios.sh.

Zero of three preconditions are met. Under conservative tactical-review
policy, PGS cannot advance to eligible_for_review or unlocked at this
baseline.

This packet is governance-only and read-only. It does not consume a
class transition, does not generate pgs code, does not modify the
framework/pgs_* surface, and does not modify
tactical_unlock_criteria.json.

## Consequences

- governance/tactical_unlock_criteria.json is unchanged.
- governance/tactical_family_classification.json is unchanged.
- No pgs_ code is created.
- No pgs_* regression fixture is created.
- next_package_class.json#current_allowed_class remains "ratification_only".

## Invariants explicitly preserved

- **LOB-W3 pause under
  governance/authority_adr_0003_lob_w3_classification.md remains in
  effect as a system-wide invariant.** This ADR is for the PGS family
  only and does not touch LOB or LOB-W3 state.
- No other family is evaluated or changed.
- Canonical phases remain 0..6.
- Phase 4 and Phase 5 remain open and unadvanced.
- No framework/ byte changes.
- No bin/ byte changes.
- No existing ADR byte changes.
- No generator source byte changes.
- Living generator-owned artifacts classified by
  governance/authority_adr_0009_living_generator_artifacts.md remain
  unchanged because this packet adds no new framework primitive consumers.

## Next review

A later TREV-PGS-2 packet may be opened only after separate non-review
packets commit all of the following:
- canonical Phase 5 advanced to closed_ratified (or otherwise
  explicitly authorized to admit PGS work) via a separate non-review
  packet,
- at least one framework/pgs_*.py file with a real static import of a
  Phase-1 runtime primitive such that
  runtime_adoption_report.json tactical_family_adoption for pgs shows
  adopting_files >= 1, and
- at least one tests/test_pgs_*.py regression scenario wired into
  tests/run_offline_scenarios.sh covering PGS governance helpers.

This ADR does not authorize any of that follow-on work.

## Supersedes

None.
