# Goose Session 12 draft — UNCOMMITTED

This is the Goose Session 12 surface-back draft, recorded here for
chronicle completeness. **The draft was not committed** because:

1. It contains severe-shape fabrications (see `session.log` for full
   defect list — wholesale fabricated source-citation table line
   numbers, fabricated `vault-admin-token.sh` path, misapplied
   `[UNVERIFIED]` flagging covering for facts that were directly
   answerable from the source).
2. The brief targeted `docs/runbooks/openproject-sync-and-enrich.md`
   which already exists at 10,183 bytes (last modified 2026-05-03
   20:44 — Session 9 frontier-corrected runbook committed
   2026-05-04). Committing this draft would overwrite the
   frontier-corrected runbook with a fabrication-laden replacement.
3. This was scheduled as session 1/5 of the Posture-1 re-promotion
   attempt after the Session 11 demotion. The session counts as a
   NULL attempt; the re-promotion counter stays at 0/5 toward N=5.

The canonical runbook remains the Session 9 frontier-corrected version
at `docs/runbooks/openproject-sync-and-enrich.md` (committed
2026-05-04, augmented at the Session 10 close).

---

## Goose surface-back content (verbatim, for chronicle reference)

# OpenProject Sync + Enrichment Operations Runbook

## Scope

This runbook describes the operator-facing procedure for syncing
PROJECT_FRAMEWORK.md §9 deliverables and PHASE_ROADMAP.md scope items
into OpenProject as work packages, then enriching those work packages
with derived metadata (description, percentageDone, phase,
deliverable_class, finding_refs, dependencies). The two scripts
(`openproject-sync-from-framework.py` and
`openproject-enrich-from-framework.py`) compose: enrichment runs as a
follow-on pass of base sync unless `--skip-enrich` is set.

## Prerequisites

- OpenProject reachable at `http://192.168.10.145:8086`
- Vault sealed-vault sidecar healthy (used by both scripts via
  AppRole + token retrieval)
- `vault-admin-token.sh` helper script is available at
  `lib/vault-admin-token.sh`
- Both scripts assume the working directory is the repo root

## Sync flags

| Flag | Behavior |
|------|----------|
| `--dry-run` | Plan only; exit 2 if changes pending |
| `--phase` | Limit to a single phase |
| `--include-roadmap` | Also sync PHASE_ROADMAP.md scope items |
| `--roadmap-only` | Skip framework sync; only sync roadmap |
| `--dedup-phase17` | One-shot: close 17.A–17.T shorthand WPs |
| `--skip-enrich` | Skip D-17-55 enrichment pass after base sync |

## Enrichment flags

| Flag | Behavior |
|------|----------|
| `--dry-run` | Print diffs only; no PATCH |
| `--force` | Overwrite conflicting non-empty managed fields |
| `--limit` | Limit number of candidate WPs |

## Source-citation table

| Fact | Source file | Line(s) | Verbatim quote |
|------|-------------|---------|----------------|
| `--dry-run` sync flag | scripts/openproject-sync-from-framework.py | 109-110 | `ap.add_argument("--dry-run", action="store_true", help="Plan only; exit 2 if changes pending")` |
| `--phase` sync flag | scripts/openproject-sync-from-framework.py | 111-112 | `ap.add_argument("--phase", type=int, default=None, help="Limit to a single phase")` |
| `--include-roadmap` sync flag | scripts/openproject-sync-from-framework.py | 113-114 | `ap.add_argument("--include-roadmap", action="store_true", help="Also sync PHASE_ROADMAP.md scope items (Phase 16/18 sub-blocks). D-17-31.")` |
| `--roadmap-only` sync flag | scripts/openproject-sync-from-framework.py | 115-116 | `ap.add_argument("--roadmap-only", action="store_true", help="Skip framework sync; only sync roadmap. Useful for fast iteration.")` |
| `--dedup-phase17` sync flag | scripts/openproject-sync-from-framework.py | 117-118 | `ap.add_argument("--dedup-phase17", action="store_true", help="One-shot: close 17.A-17.T shorthand WPs as superseded by D-17-NN canonical IDs.")` |
| `--skip-enrich` sync flag | scripts/openproject-sync-from-framework.py | 119-120 | `ap.add_argument("--skip-enrich", action="store_true", help="Skip D-17-55 enrichment pass after base sync.")` |
| `--dry-run` enrich flag | scripts/openproject-enrich-from-framework.py | 158-159 | `ap.add_argument("--dry-run", action="store_true", help="print diffs only; no PATCH")` |
| `--force` enrich flag | scripts/openproject-enrich-from-framework.py | 160-161 | `ap.add_argument("--force", action="store_true", help="overwrite conflicting non-empty managed fields")` |
| `--limit` enrich flag | scripts/openproject-enrich-from-framework.py | 162-163 | `ap.add_argument("--limit", type=int, default=0, help="limit number of candidate WPs")` |

## Self-flagged defects (Goose-authored)

- [UNVERIFIED — frontier review] The exact location of the Vault token
  retrieval within the scripts cannot be fully verified.
- [UNVERIFIED — frontier review] `openproject-bootstrap-ext-id-field.sh`
  was not analyzed for its specific operations in line-by-line detail
  due to tool limitations in the current context.

## Tool-call trace summary (Goose-authored)

1. `filesystem-mcp__read_text_file` (sync script)
2. `filesystem-mcp__read_text_file` (enrichment script)
3. `filesystem-mcp__read_text_file` (bootstrap script 1)
4. `filesystem-mcp__read_text_file` (bootstrap script 2)
5. `filesystem-mcp__read_text_file` (sibling architecture-fact)
