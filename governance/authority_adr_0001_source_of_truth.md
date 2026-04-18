# ADR 0001 — Machine-Readable Source of Truth for Governance Authority

Status: accepted (RECON-W1)
Owner: governance/README.md

## Context

The repository accumulates authority claims in multiple places:

- `docs/claude-code-roadmap.md` — narrative roadmap written as prose
- `docs/version15-master-roadmap.md` — historical/legacy narrative from an
  earlier planning era
- `docs/system_milestone_roadmap.md` — cross-cutting milestone narrative that
  blends multiple product surfaces
- `config/promotion_manifest.json` — legacy tactical release manifest used by
  `promotion/manifest.py` (Stage/Manager/RAG worldview)

These artifacts disagree about what phase the project is in, which helpers are
authorized, and what the runtime contract looks like. None of them is a
machine-readable authority. No ADR pack, CMDB-lite, autonomy scorecard, or
definition-of-done file has previously been ratified.

Recent tactical packages (EO, ED, MC, LOB, ORT, PGS) have also been referred to
as if they were canonical phases, which creates the risk of minting canonical
phase numbers above 6 without governance authorization.

## Decision

1. The canonical machine-readable authority for the coding-runtime side of this
   repository lives under `governance/`:
   - `governance/canonical_roadmap.json`
   - `governance/current_phase.json`
   - `governance/runtime_contract_version.json`
   - `governance/phase_gate_status.json`
   - `governance/runtime_adoption_report.json`
   - `governance/tactical_family_classification.json`
2. `docs/claude-code-roadmap.md` is narrative roadmap only. It may inform
   governance artifacts but does not override them.
3. `docs/version15-master-roadmap.md` is historical / legacy narrative only.
4. `docs/system_milestone_roadmap.md` is out of scope for this repository's
   coding-runtime authority.
5. `config/promotion_manifest.json` and its consumer `promotion/manifest.py`
   remain legacy tactical release authority. They are frozen pending an
   explicit migration package. RECON-W1 does not migrate them.
6. The governance JSON artifacts are generated deterministically by
   `bin/governance_reconcile.py` and verified by `tests/test_governance_reconcile.py`.
7. The allowed canonical phase range is `0..6` inclusive. Canonical phase
   numbers above 6 are not permitted by this ADR.

## Consequences

- Future reconciliation packages must update the `governance/*.json` files via
  `bin/governance_reconcile.py --write` and commit the result.
- Disagreements between narrative docs and `governance/*.json` are resolved in
  favor of `governance/*.json`.
- The legacy promotion manifest remains operational for existing callers; new
  callers must not depend on it for phase authority.
- Human-readable overview lives in `governance/README.md`. It is a map, not a
  source of truth.

## Supersedes

- Any implicit authority previously assigned to `docs/claude-code-roadmap.md`,
  `docs/version15-master-roadmap.md`, `docs/system_milestone_roadmap.md`, or
  `config/promotion_manifest.json` for the purpose of canonical phase or
  runtime contract decisions.
