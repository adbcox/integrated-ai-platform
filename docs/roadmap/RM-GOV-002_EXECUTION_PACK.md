# RM-GOV-002 — Execution Pack

## Title

**RM-GOV-002 — Recurring full-system integrity review for naming consistency, duplicates, mismatches, and synchronization hygiene**

## Canonical relationship

- Master roadmap authority: `docs/roadmap/ROADMAP_MASTER.md`
- Normalized backlog entry: `docs/roadmap/ROADMAP_INDEX.md`
- Standards: `docs/roadmap/STANDARDS.md`
- Related items: `RM-GOV-001`, `RM-GOV-003`

## Objective

Create a recurring integrity review process that detects naming drift, duplicate concepts, sync failures, and backlog inconsistencies before they accumulate.

## Why this matters

The roadmap system only stays reliable if it is periodically audited for internal consistency and sync hygiene.

## Required outcome

- recurring integrity checks
- duplicate and mismatch detection
- sync-gap reporting
- repair recommendations with roadmap IDs

## Recommended posture

- treat integrity review as a maintenance system, not a one-time cleanup
- compare roadmap, execution docs, and linked artifacts systematically
- preserve audit outputs for trend tracking

## Required artifacts

- integrity report
- duplicate/mismatch list
- sync-gap report
- remediation recommendation list

## Best practices

- audit by canonical ID and canonical names
- preserve machine-readable issue classes
- separate naming drift from missing-linkage failures
- review both roadmap docs and downstream execution artifacts

## Common failure modes

- duplicated roadmap items under different titles
- legacy docs treated as canonical by accident
- changed priority in one file but not another
- chat-only items missing from the canonical roadmap

## Recommended first milestone

Build a recurring integrity report that checks ID presence, naming consistency, duplicate titles/concepts, and master/index sync status.
