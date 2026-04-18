# ADR 0009 — Living Generator-Owned Artifacts and Acceptance of CAP-P2-CLOSE-1 / RECON-W2B

## Status

Accepted (RECON-W2C-LIVING-GENERATOR-RATIFY-1).

Baseline commits:
- RECON-W1: `53ae4d4f177b176a7bffaa63988f63fa0efa622c`
- RECON-W2A: `595dc8750ed671fb23d3cec0be434c76dad818f5`
- CAP-P2-CLOSE-1: `0981c22b17a87d3e6548c0b337a40305c068c3d3`
- RECON-W2B-CAP-P2-RATIFY-1: `864945ce43edd5f9bd7385eeb26740eabe94d969`

## Context

Three governance JSON files are produced entirely by static-scan generators
whose inputs are the committed tracked Python sources of the repository:

- `governance/schema_contract_registry.json` — produced by
  `bin/governance_phase0_closer.py`, which enumerates schema consumer modules
  by scanning committed Python files for imports of `framework/*_schema.py`.
- `governance/runtime_contract_version.json` — produced by
  `bin/governance_reconcile.py`, which derives `contract_version` from the
  sha256 of each runtime primitive and records `observed_adoption_paths`
  from committed static imports.
- `governance/runtime_adoption_report.json` — produced by
  `bin/governance_reconcile.py`, which enumerates `direct_runtime_paths` and
  per-family adoption by static import scan.

Any committed change to the set of tracked consumer modules — for example,
the addition of `bin/governance_phase2_evidence_recorder.py` and
`tests/capability/conftest.py` in CAP-P2-CLOSE-1 — legitimately changes the
output of these generators. Attempting to freeze the bytes of any of the
three files while tracked consumers change is incompatible with deterministic
and idempotent governance. It also breaks existing idempotence tests,
specifically `tests/test_governance_phase0_closure.py::test_closer_check_is_idempotent`.

RECON-W2B-CAP-P2-RATIFY-1 listed `schema_contract_registry.json` in its
forbidden-edit invariant. The registry nevertheless had to be regenerated
for `governance-test` to pass after CAP-P2-CLOSE-1 added legitimate new
framework-schema consumers. This ADR resolves that scope conflict formally.

## Decision

1. The following three files are formally classified as living
   generator-owned artifacts. Their bytes must track the committed tree
   and are owned by the listed generators:
   - `governance/schema_contract_registry.json` — owner
     `bin/governance_phase0_closer.py`.
   - `governance/runtime_contract_version.json` — owner
     `bin/governance_reconcile.py`.
   - `governance/runtime_adoption_report.json` — owner
     `bin/governance_reconcile.py`.
   No packet may "freeze" any of these three artifacts against legal
   consumer drift. Future packets that forbid editing them must read that
   prohibition as "no hand edits and no generator-logic changes," not as
   "bytes must not change."

2. Phase 0 closure is invariant under legal consumer drift. Phase 0 remains
   `closed_ratified`. The structural predicates that govern Phase 0 closure
   live in `governance/phase0_closure_decision.json` and are not modified
   by this packet. A consumer-count drift in an already-classified schema
   consumer is not, by itself, a reopening event. This ADR does not claim
   to be the Phase 0 ratifying ADR and does not modify Phase 0 state.

3. Acceptance of CAP-P2-CLOSE-1 and RECON-W2B into the post-RECON-W2A
   accepted baseline is recorded here. The accepted consequences (already
   present at HEAD) are preserved unchanged:
   - Phase 2 = `closed_ratified`
   - `current_allowed_class` = `ratification_only`
   - every tactical family remains `locked`
   - LOB-W3 remains paused under `authority_adr_0003_lob_w3_classification.md`
   ADR 0008 remains the authoritative Phase 2 closure record. This ADR
   does not re-ratify Phase 2.

4. `governance/living_generator_artifacts.json` is the machine-readable
   acceptance record for the living-artifact classification, the Phase 0
   invariance statement, and the acceptance of CAP-P2-CLOSE-1 and
   RECON-W2B.

## Consequences

- Future packets can cite `governance/living_generator_artifacts.json` to
  distinguish generator-owned outputs from hand-curated governance JSON.
- Running `make governance-ratify` and `make governance-check` remain the
  authoritative idempotence gates. A diff that appears only in a living
  generator-owned artifact after a committed consumer change is not a
  governance regression; it is the generator catching up to the tree.
- No tactical family is unlocked by this ADR.
- No framework edits are introduced by this ADR.
- No existing ADR is superseded. ADR 0005 continues to describe the
  original RECON-W2 partial adoption; ADR 0008 continues to describe the
  Phase 2 closure decision; ADR 0009 describes only the living-artifact
  rule and the acceptance event.

## Supersedes

- The RECON-W2B-CAP-P2-RATIFY-1 forbidden-edit invariants on the three
  living generator-owned artifacts listed above. No other RECON-W2B
  invariants are affected.

## Validation evidence

- `make governance-check` passes at the acceptance commit.
- `make governance-ratify` passes at the acceptance commit.
- `make governance-test` passes at the acceptance commit.
- `python3 -m unittest tests.test_governance_living_artifacts` passes.
- `make capability-phase2-run` passes.
- `make capability-phase2-record` passes; `governance/phase2_closure_evidence.json`
  is unchanged.
- `make check` and `make quick` pass.
- `git diff framework/` is empty.
- Only the four packet-allowed paths are modified by this packet.
