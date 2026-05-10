# Change Records (CR) Register

Tracks formal scope changes per the `CR-NN-NNN` taxonomy in
`docs/PROJECT_FRAMEWORK.md` §3 (and `docs/architecture-facts/identifier-conventions.md`).
Each CR documents a discrete scope-change event: cross-phase escalation,
descope, refactor crossing scope lines, or retrospective reclassification.

## Purpose

When a deliverable's scope changes after the deliverable ID is issued,
the framework's identifier-stability rule (`Labels are stable once
issued`) forbids re-using the ID for new scope. Two paths apply:

1. **Close + re-issue.** Mark the original ID `SUPERSEDED by` /
   `DEFERRED to`, issue a new ID for the new scope.
2. **Escalate via CR.** When the change is a scope-boundary cross
   (deliverable conceptually belongs to a different phase than the one
   it landed in), file a CR documenting the disposition. The
   deliverable's intrinsic status (`DONE` / `IN PROGRESS` / etc.) is
   preserved; the CR overlays the disposition.

Path (2) is what this register handles.

## Filing convention

- One file per CR: `CR-NN-NNN-<slug>.md`
- `NN` = source phase (the phase the change originates from)
- `NNN` = zero-padded sequence within the phase (001, 002, ...)
- Slug is short, lowercase, hyphen-separated
- Example: `CR-17-001-aider-agentic-stack-escalation.md`

## YAML frontmatter (required fields)

```yaml
---
cr: CR-NN-NNN
title: <one-line description>
status: open | applied | rejected | superseded
source_phase: Phase-NN
target_phase: Phase-NN | n/a
discovered: YYYY-MM-DD
applied: YYYY-MM-DD
affected_deliverables: [D-NN-MM, ...]
summary: <one line>
---
```

## Section structure

- `## Summary` — 2-3 sentences
- `## Affected deliverables` — table or list with title + status
- `## Rationale` — why the change is needed; why it wasn't caught earlier
- `## Disposition` — what changes (deliverables move, scope shrinks, etc.)
- `## Cross-references` — related KIs, doctrine docs, prior CRs, commits
- `## Audit trail` — timestamp + brief log of state transitions

## Relationship to PROJECT_FRAMEWORK.md §9

When a CR escalates deliverables across phases, each affected
deliverable's §9 row gets a reference note appended:
`→ ESCALATED-TO-PHASE-NN via CR-NN-NNN (date)`. The intrinsic status
column (DONE / IN PROGRESS / etc.) is NEVER overwritten — the CR is
an overlay, not a replacement.

## Retrospective CRs

If a scope-change happened before the CR mechanism was actively
enforced (as in CR-17-001 through CR-17-006, where 38+ deliverables
had drifted into Phase 17 scope before any CR was authored), the CR
is authored retrospectively. The `applied` field reflects the original
drift date (typically equal to or earlier than `discovered`).
Retrospective nature is named explicitly in the Rationale section.

## Index (as of 2026-05-11)

| CR | Title | Status | Affects |
|---|---|---|---|
| CR-17-001 | Aider agentic stack escalation | applied | 15 deliverables (D-17-93/94/95/96/97/101/103/104/109/110/111/133/134/135 + D-17-136) |
| CR-17-002 | Music arr-stack escalation | applied | 5 deliverables (D-17-87/98/100/102/112) |
| CR-17-003 | Arr-stack expansion + observability | applied | 6 deliverables (D-17-46/47/105/106/107/114) |
| CR-17-004 | Codex / multifile orchestration | applied | 8 deliverables (D-17-117/118/124/125/126/127/128/129) |
| CR-17-005 | Goose Phase-13+ stack | applied | 2 deliverables (D-17-90/91) |
| CR-17-006 | Misc Phase-18 escalations | applied | 3 deliverables (D-17-35/52/76) |

Total: 39 deliverables escalated retrospectively from Phase 17 to Phase 18.
