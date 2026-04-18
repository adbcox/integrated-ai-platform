# ADR 0002 — Tactical Family Classification

Status: accepted (RECON-W1)
Owner: governance/tactical_family_classification.json

## Context

Tactical package families have been created throughout the repository under the
labels EO, ED, MC (including the `multi_phase_*` helper surface), LOB (the
`live_bridge_*` surface), ORT, and PGS. These families have been referred to in
conversations and in commit messages as if they were canonical phases, which
risks minting canonical phase numbers above the authorized range of 0..6.

The repository now has a machine-readable authority pack (see ADR 0001). That
pack requires a consistent classification mechanism for tactical families so
that:

- tactical families are never confused with canonical phases
- each family has a well-defined promotion/retirement path
- governance can measure runtime-primitive adoption per family

## Decision

1. Tactical families are never canonical phases. They must not appear in the
   `phases[]` array of `governance/canonical_roadmap.json`. They must not
   carry a `phase_id` attribute.
2. Every tactical family is classified as one of:
   - `canonically_authorized_family` — family is ratified as canonical work
     under a specific canonical phase; package work may proceed
   - `provisional_precursor` — committed code exists but no canonical phase
     authority ratifies it; retained in-tree, no new tactical packages
   - `paused_pending_reconciliation` — explicit decision to pause; no new
     tactical packages and code may be retired by a later reconciliation
3. Promotion from `provisional_precursor` to `canonically_authorized_family`
   requires all of:
   - the target canonical phase is open and authorizes the family
   - the family has measurable runtime-primitive adoption in
     `governance/runtime_adoption_report.json`
   - the family has named offline regression coverage
4. Demotion to `paused_pending_reconciliation` requires an ADR in
   `governance/` that names the family and the reason.
5. The classification values for EO, ED, MC, LOB, ORT, and PGS at as_of_commit
   are all `provisional_precursor`. See
   `governance/tactical_family_classification.json` for the canonical record.

## Consequences

- New tactical packages for a family in `provisional_precursor` or
  `paused_pending_reconciliation` require an ADR to unlock them.
- Existing committed code in tactical families is not modified by this ADR.
- The legacy promotion manifest (`config/promotion_manifest.json`) is a
  separate tactical release authority and is not treated as a canonical phase
  advance.

## Supersedes

- Any prior implicit assumption that EO, ED, MC, LOB, ORT, or PGS were
  canonical phases, or that committing helpers under these prefixes advanced
  the canonical phase counter.
