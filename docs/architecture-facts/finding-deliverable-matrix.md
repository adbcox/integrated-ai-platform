# Finding-to-Deliverable Matrix (Findings 1-16)

Date: 2026-05-04
Deliverable: D-17-65
Scope: Cross-reference matrix for Findings 1-16 in
`integration-audit-doctrine.md` mapped to deliverables cited across
`docs/` + `scripts/`.

## Method

1. Parsed Findings 1-16 from
   `docs/architecture-facts/integration-audit-doctrine.md`.
2. Scanned `docs/` + `scripts/` for `Finding N` and `F<N>` references.
3. Mapped references to deliverables (`D-NN-NN`) by:
   - file ownership (`.../d-NN-NN/...` path), and/or
   - explicit `D-NN-NN` references in the same artifact.
4. Added explicit originating WPs from finding headers where present.

## View A — Finding -> Deliverables

| Finding | Deliverables citing/referencing | Count |
|---|---|---:|
| F1 | D-15-04, D-15-07, D-17-04, D-17-10, D-17-12, D-17-13, D-17-14, D-17-16, D-17-18, D-17-19, D-17-21, D-17-23, D-17-25, D-17-26, D-17-28, D-17-30, D-17-31, D-17-32, D-17-36, D-17-38, D-17-44, D-17-51, D-17-53, D-17-54, D-17-57 | 25 |
| F2 | D-15-04, D-15-07, D-17-04, D-17-12, D-17-13, D-17-18, D-17-21, D-17-25, D-17-30, D-17-31, D-17-32, D-17-34, D-17-51, D-17-57 | 14 |
| F3 | D-15-04, D-15-07, D-17-04, D-17-12, D-17-13, D-17-17, D-17-18, D-17-21, D-17-25, D-17-29, D-17-31, D-17-32, D-17-34, D-17-43, D-17-44, D-17-57 | 16 |
| F4 | D-17-04, D-17-12, D-17-13, D-17-17, D-17-18, D-17-21, D-17-25, D-17-31, D-17-32, D-17-34, D-17-43, D-17-44, D-17-57 | 13 |
| F5 | D-17-04, D-17-12, D-17-16, D-17-18, D-17-25, D-17-31, D-17-32, D-17-34, D-17-35, D-17-36, D-17-37, D-17-39, D-17-40, D-17-57 | 14 |
| F6 | D-17-12, D-17-13, D-17-21, D-17-26, D-17-38, D-17-44, D-17-51, D-17-53, D-17-54, D-17-57 | 10 |
| F7 | D-17-12, D-17-32, D-17-34, D-17-36, D-17-57 | 5 |
| F8 | D-17-12, D-17-16, D-17-29, D-17-32, D-17-36 | 5 |
| F9 | D-17-09, D-17-12, D-17-21, D-17-56 | 4 |
| F10 | D-17-12, D-17-16, D-17-32, D-17-36 | 4 |
| F11 | D-17-21, D-17-29, D-17-38, D-17-44, D-17-46, D-17-47, D-17-49, D-17-53 | 8 |
| F12 | D-17-12, D-17-16, D-17-32, D-17-36 | 4 |
| F13 | D-17-12 | 1 |
| F14 | D-17-12, D-17-13, D-17-21, D-17-38, D-17-44, D-17-51, D-17-53, D-17-54, D-17-56, D-17-57 | 10 |
| F15 | D-17-13, D-17-21, D-17-38, D-17-44, D-17-51, D-17-53, D-17-54, D-17-57 | 8 |
| F16 | D-17-51, D-17-53, D-17-58, D-17-59 | 4 |

## View B — Deliverable -> Findings (density)

High-density deliverables (3+ findings):

| Deliverable | Findings | Count |
|---|---|---:|
| D-17-12 | F1,F2,F3,F4,F5,F6,F7,F8,F9,F10,F12,F13,F14 | 13 |
| D-17-21 | F1,F2,F3,F4,F6,F9,F11,F14,F15 | 9 |
| D-17-32 | F1,F2,F3,F4,F5,F7,F8,F10,F12 | 9 |
| D-17-57 | F1,F2,F3,F4,F5,F6,F7,F14,F15 | 9 |
| D-17-13 | F1,F2,F3,F4,F6,F14,F15 | 7 |
| D-17-44 | F1,F3,F4,F6,F11,F14,F15 | 7 |
| D-17-36 | F1,F5,F7,F8,F10,F12 | 6 |
| D-17-51 | F1,F2,F6,F14,F15,F16 | 6 |
| D-17-53 | F1,F6,F11,F14,F15,F16 | 6 |
| D-17-04 | F1,F2,F3,F4,F5 | 5 |
| D-17-16 | F1,F5,F8,F10,F12 | 5 |
| D-17-18 | F1,F2,F3,F4,F5 | 5 |
| D-17-25 | F1,F2,F3,F4,F5 | 5 |
| D-17-31 | F1,F2,F3,F4,F5 | 5 |
| D-17-34 | F2,F3,F4,F5,F7 | 5 |
| D-17-38 | F1,F6,F11,F14,F15 | 5 |
| D-17-54 | F1,F6,F14,F15 | 4 |
| D-17-09 | F9 | 1 |
| D-17-10 | F1 | 1 |
| D-17-14 | F1 | 1 |
| D-17-17 | F3,F4 | 2 |
| D-17-19 | F1 | 1 |
| D-17-23 | F1 | 1 |
| D-17-26 | F1,F6 | 2 |
| D-17-28 | F1 | 1 |
| D-17-29 | F3,F8,F11 | 3 |
| D-17-30 | F1,F2 | 2 |
| D-17-35 | F5 | 1 |
| D-17-37 | F5 | 1 |
| D-17-39 | F5 | 1 |
| D-17-40 | F5 | 1 |
| D-17-43 | F3,F4 | 2 |
| D-17-46 | F11 | 1 |
| D-17-47 | F11 | 1 |
| D-17-49 | F11 | 1 |
| D-17-56 | F9,F14 | 2 |
| D-17-58 | F16 | 1 |
| D-17-59 | F16 | 1 |
| D-15-04 | F1,F2,F3 | 3 |
| D-15-07 | F1,F2,F3 | 3 |

## Anomaly Catalog

### Orphan findings

- None. All Findings 1-16 have at least one deliverable citation.

### Single-point finding

- F13 currently maps to a single deliverable (`D-17-12`) in this scan.

### Density skew

- `D-17-12` is a citation outlier (13 findings), driven largely by
  benchmark/task-set artifacts that carry many historical cross-refs.

### Citation noise / weak ownership artifacts

The following artifacts mention findings but do not carry explicit
deliverable ownership in-path or in-body D-IDs (therefore excluded from
owner-mapped matrix rows):

- `docs/phase-13/PHASE_13_FOUNDATION_AUDIT_2026-04-29.md`
- `docs/phase-13/PHASE_13_BLOCK_4C_CLOSEOUT_2026-04-29.md`
- `docs/phase-13/h1-rewire-queue.md`
- `docs/phase-13/INCREMENT_1_PHASE_C_BACKFILL_2026-04-29.md`
- `docs/phase-13/PRE_BLOCK_2_READINESS_AUDIT_2026-04-28.md`
- `docs/phase-13/INCREMENT_1_CLOSEOUT_2026-04-29.md`
- `docs/phase-13/PRE_BLOCK_2_FOUNDATION_AUDIT_2026-04-28.md`
- `docs/phase-13/INCREMENT_1_DCN_AUDIT_2026-04-29.md`
- `docs/phase-14/PHASE_14_BLOCK_D_DOC_CLOSEOUT_2026-04-29.md`
- `docs/phase-14/ARCHITECTURE_CLOSEOUT_PLAN_2026-04-29.md`
- `docs/phase-15/COMPREHENSIVE_AUDIT_2026-05-01.md`
- `docs/phase-15/COMPREHENSIVE_AUDIT_VALIDATION_2026-05-01.md`
- `docs/_archive/plane-connector-usage.md`
- `scripts/backfill-plane-labels.py`

### Finding metadata consistency gap

- Findings 6-13 are fully present but several do not include the same
  explicit `Date` / `Originating WP` header fields used by Findings
  1-5 and 14-16.
