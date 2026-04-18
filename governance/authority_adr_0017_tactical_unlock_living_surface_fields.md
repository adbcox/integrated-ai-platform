# ADR 0017 — Tactical Unlock Criteria Hybrid Ownership: Decision Fields vs. Living Surface Fields

Status: accepted (RECON-W2D-MC-RATIFIER-BOUNDARY-1)
Owner: governance/mc_seed_reconciliation_note.json
Baseline commits:
- RECON-W1:            53ae4d4f177b176a7bffaa63988f63fa0efa622c
- RECON-W2A:           595dc8750ed671fb23d3cec0be434c76dad818f5
- RECON-W2C:           6b2446180a4d1e9194ef682aacd33fc12f1f4c46
- TREV-MC-1-AMEND:     dcb944141f1e8d1a01a991f44546ad99a774511c
- MC-SEED-1:           b9cdf651e0495a463cc130ec81d65256cfe68d5f

## Context

`governance/tactical_unlock_criteria.json` has, since RECON-W2, mixed
two logically distinct kinds of fields inside each family row:

- **Decision fields** such as `unlock_state`,
  `currently_met_preconditions`, `review_packet_required`,
  `canonical_phase_dependency`, and `unlock_preconditions`. These
  change only when a per-family review packet (ADR 0006) or an
  explicit tactical unlock packet mutates them.
- **Surface measurement fields** — at present only `total_family_files`
  — which are derived by scanning the committed tree for files
  matching each family's prefixes and counting them.

MC-SEED-1 made this latent contradiction manifest: adding
`framework/multi_phase_permission_gate.py` (a legitimate additive
MC helper) caused `bin/governance_unlock_evaluator.py` to observe
`total_family_files` for MC change from 271 to 272, and therefore to
produce a diff in `governance/tactical_unlock_criteria.json` on
`make governance-ratify`. Prior packets' forbidden-edit invariants on
`tactical_unlock_criteria.json` were being read as byte-freeze, which
is incompatible with tracking live repo surface.

ADR 0009 already classifies
`governance/schema_contract_registry.json`,
`governance/runtime_contract_version.json`, and
`governance/runtime_adoption_report.json` as living generator-owned
artifacts. This ADR applies the same principle to the specific
subfield(s) of `tactical_unlock_criteria.json` that are derived by
static scan.

## Decision

1. `governance/tactical_unlock_criteria.json` is a hybrid artifact:
   - **Decision-owned fields** (per family row): `unlock_state`,
     `currently_met_preconditions`, `review_packet_required`,
     `canonical_phase_dependency`, `unlock_preconditions`,
     `prefixes`, `family_id`, `notes`, and (where present) `adr_ref`.
     These remain governance-owned and may only change through an
     ADR 0006 review packet or a tactical unlock packet.
   - **Living generator-owned subfields**: `total_family_files` and
     any other purely counted surface field produced by a static
     repo scan. These re-render mechanically on every
     `make governance-ratify` to reflect the committed tree and may
     drift without signalling any decision change.

2. Future packets that forbid editing
   `governance/tactical_unlock_criteria.json` must read the
   prohibition as "no hand edits; no change to any decision-owned
   field; no generator-logic changes" — not as "the file must be
   byte-identical across commits that legitimately change the
   family surface."

3. `bin/governance_unlock_evaluator.py` is the designated owner of
   the living surface subfields. No other generator may write them.

4. **MC-SEED-1 is accepted as-is.** MC remains locked and
   `provisional_precursor`. The seeded 2-of-3 precondition state
   recorded in `governance/mc_unlock_seed_evidence.json` is preserved.
   `governance/mc_seed_reconciliation_note.json` records this
   acceptance in machine-readable form.

5. This ADR does **not**:
   - unlock any tactical family,
   - change `current_allowed_class` (remains `ratification_only`),
   - modify ADR 0006's per-family review requirement,
   - modify any per-family review JSON or ADR decision,
   - advance any canonical phase.

## Consequences

- `make governance-ratify` followed by `make governance-check` can now
  round-trip cleanly across additive MC-family file landings without
  producing ambiguous DIFF lines on `tactical_unlock_criteria.json`.
- Per-family review tests (`tests/test_governance_*_family_unlock_review.py`)
  must assert decision fields, not surface counts.
- A later TREV-MC-2 packet can mechanically re-evaluate MC against
  the three unlock preconditions. Under current authority MC still
  remains locked because canonical Phase 4 is `open`.

## Invariants explicitly preserved

- No tactical family unlocked.
- `governance/tactical_family_classification.json` unchanged.
- `governance/next_package_class.json` unchanged; `current_allowed_class`
  remains `ratification_only`.
- `governance/phase2_adoption_decision.json` unchanged; `decision`
  remains `closed`.
- No framework/ edits.
- No Phase-1 primitive edited.
- LOB-W3 remains paused under
  `governance/authority_adr_0003_lob_w3_classification.md`.
- Canonical phases remain 0..6.

## Supersedes

- The byte-freeze interpretation of `tactical_unlock_criteria.json`
  implicit in RECON-W2B and re-asserted by MC-SEED-1's forbidden-edit
  list. Living-surface subfields are formally reclassified here.
