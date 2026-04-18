# Governance Authority (machine-readable)

This directory holds the machine-readable authority for the coding-runtime
side of the repository. The JSON files here are the source of truth for
canonical phase, runtime contract, gate status, and tactical family
classification. The ADR files record the decisions that bind them.

Narrative roadmaps under `docs/` are historical or advisory only. The legacy
`config/promotion_manifest.json` remains tactical release authority and is
frozen pending explicit migration (see ADR 0001).

## Authority files

| File | Purpose |
| --- | --- |
| `canonical_roadmap.json` | Canonical phases 0..6 and their statuses |
| `current_phase.json` | Current canonical phase, next allowed package class, blocked package classes and families |
| `runtime_contract_version.json` | Runtime primitive surface, hashes, contract version, observed adoption paths |
| `phase_gate_status.json` | Gate table for canonical phases 0..6 |
| `runtime_adoption_report.json` | Direct and per-tactical-family adoption of runtime primitives |
| `tactical_family_classification.json` | Canonical classification of EO, ED, MC, LOB (live_bridge), ORT, PGS |

## Decisions

- [ADR 0001 — Machine-Readable Source of Truth](authority_adr_0001_source_of_truth.md)
- [ADR 0002 — Tactical Family Classification](authority_adr_0002_tactical_family_classification.md)
- [ADR 0003 — LOB-W3 Classification](authority_adr_0003_lob_w3_classification.md)
- [governance/living_generator_artifacts.json](living_generator_artifacts.json) — machine-readable classification of living generator-owned artifacts and acceptance record for CAP-P2-CLOSE-1 / RECON-W2B
- [governance/authority_adr_0009_living_generator_artifacts.md](authority_adr_0009_living_generator_artifacts.md) — narrative authority for the living-artifact classification and acceptance event
- [governance/authority_adr_0010_eo_family_unlock_review.md](authority_adr_0010_eo_family_unlock_review.md) — per-family tactical review for EO (TREV-EO-1); decision: remains_locked at baseline 6b244618
- [governance/authority_adr_0011_ed_family_unlock_review.md](authority_adr_0011_ed_family_unlock_review.md) — per-family tactical review for ED (TREV-ED-1); decision: remains_locked at baseline ae4077bc8b48b445e6e783e772e6ccc58c53b525

## How to update

1. `make governance-write` — regenerate the JSON artifacts from live repo
   state (`bin/governance_reconcile.py --write`).
2. `make governance-check` — validate the JSON artifacts match freshly
   computed state and pass schema checks.
3. `make governance-test` — run the offline pytest coverage.

## Scope guarantees

- Canonical phases are limited to 0..6. EO, ED, MC, LOB, ORT, and PGS are
  tactical families and are never canonical phases.
- `bin/governance_reconcile.py` writes only under `governance/` and performs
  no network I/O.
- `generated_at` is deterministic per pinned `as_of_commit`, so `--write`
  followed by `--check` is idempotent.
