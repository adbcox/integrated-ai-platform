# ADR 0013 — LIVE_BRIDGE Family Tactical Unlock Review (first-pass, remains_locked)

Status: accepted (TREV-LIVE_BRIDGE-1)
Owner: governance/live_bridge_family_unlock_review.json
Baseline commits:
- RECON-W1: 53ae4d4f177b176a7bffaa63988f63fa0efa622c
- RECON-W2A: 595dc8750ed671fb23d3cec0be434c76dad818f5
- RECON-W2C: 6b2446180a4d1e9194ef682aacd33fc12f1f4c46
- TREV-EO-1 baseline: ae4077bc8b48b445e6e783e772e6ccc58c53b525
- TREV-ED-1 baseline: 9c2420736e9542596b0d37c581cef3cba7fd2402
- TREV-MC-1 baseline: 9c2420736e9542596b0d37c581cef3cba7fd2402
- TREV-LIVE_BRIDGE-1 baseline: 3b7278b533ed9f5ea726c75a721f09cec0e959ba

## Context

governance/tactical_unlock_criteria.json records LIVE_BRIDGE as locked and
review_packet_required = true. Its `adr_ref` points at
governance/authority_adr_0003_lob_w3_classification.md, which formally
pauses LOB-W3.
governance/authority_adr_0006_tactical_unlock_criteria.md requires a
per-family review packet before any family can move out of locked. This
ADR is the first LIVE_BRIDGE-only review. This ADR does not evaluate or
modify any other family and does not lift the ADR 0003 pause.

LIVE_BRIDGE is distinctive among tactical families in that a large
evidence surface exists under `framework/live_bridge_*` (919 helper
files at this baseline per runtime_adoption_report.json), but that
surface is not wired to the shared runtime primitives, the canonical
phase that gates LOB work (Phase 6) is `open`, and the ADR 0003 pause
has not been lifted. This review records those facts and declines to
advance LOB.

## Decision

LIVE_BRIDGE remains_locked.

At baseline commit 3b7278b533ed9f5ea726c75a721f09cec0e959ba:

1. Canonical phase authority does not permit LIVE_BRIDGE work.
   Two compounding constraints are unmet:
   - governance/authority_adr_0003_lob_w3_classification.md pauses
     LOB-W3 and has not been explicitly lifted. The
     governance/tactical_unlock_criteria.json live_bridge row still
     lists "ADR 0003 pause explicitly lifted" as an unmet precondition.
   - governance/canonical_roadmap.json records Phase 6
     (controlled_expansion) as status = open and "not canonically
     authorized until Phase 5 closure". LIVE_BRIDGE has
     canonical_phase_dependency = 6 per
     governance/tactical_family_classification.json, so Phase 6
     authority does not admit LOB advancement at this baseline.
2. runtime_adoption_report.json records adopting_files = 0 and
   adopting_paths = [] for LIVE_BRIDGE. Despite 919 committed
   framework/live_bridge_* helpers, none of them statically import any
   framework runtime primitive (worker_runtime, tool_system, workspace,
   permission_engine, sandbox). Adoption is unmeasured.
3. No named offline regression scenario covers live_bridge operations.
   No tests/test_live_bridge_*.py file exists and no live_bridge case
   exists in tests/run_offline_scenarios.sh.

Zero of three preconditions are met. Under conservative tactical-review
policy, LIVE_BRIDGE cannot advance to eligible_for_review or unlocked
at this baseline.

This packet is governance-only and read-only. It does not consume a
class transition, does not generate live_bridge code, does not modify
the framework/live_bridge_* surface, does not lift the ADR 0003 pause,
and does not modify tactical_unlock_criteria.json.

## Consequences

- governance/tactical_unlock_criteria.json is unchanged.
- governance/tactical_family_classification.json is unchanged.
- No live_bridge_ code is created.
- No live_bridge_* regression fixture is created.
- next_package_class.json#current_allowed_class remains "ratification_only".

## Invariants explicitly preserved

- **LOB-W3 remains paused under
  governance/authority_adr_0003_lob_w3_classification.md.** This ADR
  does not lift that pause; lifting it requires a separate governance
  packet.
- No other family is evaluated or changed.
- Canonical phases remain 0..6.
- Phase 5 and Phase 6 remain open and unadvanced.
- No framework/ byte changes.
- No bin/ byte changes.
- No existing ADR byte changes.
- No generator source byte changes.
- Living generator-owned artifacts classified by
  governance/authority_adr_0009_living_generator_artifacts.md remain
  unchanged because this packet adds no new framework primitive consumers.

## Next review

A later TREV-LIVE_BRIDGE-2 packet may be opened only after separate
non-review packets commit all of the following:
- the ADR 0003 LOB-W3 pause has been explicitly lifted by a dedicated
  governance packet,
- canonical Phase 6 has advanced to closed_ratified (or otherwise been
  explicitly authorized to admit LOB work),
- at least one framework/live_bridge_*.py file with a real static
  import of a Phase-1 runtime primitive such that
  runtime_adoption_report.json tactical_family_adoption for
  live_bridge shows adopting_files >= 1, and
- at least one tests/test_live_bridge_*.py regression scenario wired
  into tests/run_offline_scenarios.sh covering live_bridge operations.

This ADR does not authorize any of that follow-on work.

## Supersedes

None.
