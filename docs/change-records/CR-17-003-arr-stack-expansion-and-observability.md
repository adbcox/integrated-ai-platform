---
cr: CR-17-003
title: Arr-stack expansion + observability escalated to Phase 18 §18.G
status: applied
source_phase: Phase-17
target_phase: Phase-18
discovered: 2026-05-11
applied: 2026-05-11
affected_deliverables: [D-17-46, D-17-47, D-17-105, D-17-106, D-17-107, D-17-114]
summary: 6 arr-stack observability + content-expansion deliverables retrospectively escalated to Phase 18 §18.G scope (which several already self-tagged).
---

# CR-17-003: Arr-stack expansion + observability escalation

## Summary

Six deliverables span Scraparr-based metrics observability, Bazarr
subtitle automation, Zabbix arr-stack pipeline templates, Prowlarr
indexer expansion, and Plex canonical naming. Multiple self-tag as
Phase 18 §18.G scope in their titles or doctrine text but landed
under Phase 17 IDs.

## Affected deliverables

| ID | Title | Status |
|---|---|---|
| D-17-46 | arr-stack metrics observability (Scraparr/Exportarr) | DONE |
| D-17-47 | Bazarr subtitle automation deployment (arr-stack component 18.G.5) | DONE |
| D-17-105 | Torrent/Usenet pipeline health monitoring — Zabbix templates + dashboard + alert routing | DONE |
| D-17-106 | Prowlarr indexer expansion — per-media-class coverage (TV/Movies/Music/Sports) | DONE |
| D-17-107 | Pipeline health triage — 4 active D-17-105 alerts | DONE |
| D-17-114 | Plex canonical naming alignment | IN PROGRESS |

## Rationale

D-17-46's CLAUDE.md doctrine entry literally describes it as "the
Phase 18 §18.G component-1 observability substrate." D-17-47's title
explicitly contains "18.G.5" sub-block notation. D-17-105/107 are the
Zabbix monitoring extension landed alongside D-17-46. D-17-106 and
D-17-114 are operational expansion (indexer coverage, Plex naming)
that fits §18.G/§18.L media-ops rather than Phase 17 audit theme.

All six self-identified as Phase 18 scope at authoring time but
proceeded under Phase 17 IDs because the CR mechanism wasn't
enforced. Retrospective escalation.

## Disposition

- All 6 deliverables retain their `D-17-NN` IDs.
- Intrinsic status preserved (5 DONE + 1 IN PROGRESS).
- Phase grouping moves to Phase 18 §18.G arr-stack-ops / observability.
- §9 rows gain `→ ESCALATED-TO-PHASE-18 via CR-17-003 (2026-05-11)` annotation.
- Phase 17 closeout criteria do NOT block on these deliverables.

## Cross-references

- Sibling CR: `CR-17-002` (Lidarr music arr-stack — adjacent §18.L scope).
- D-17-44 (Buildarr config-as-code) — Phase 17 in-spirit precursor; sets the F11 pattern these deliverables consume.
- D-17-38 (arr-stack integration health-check audit) — Phase 17 in-spirit precursor; defined the §18.G observability gap closed by D-17-46.

## Audit trail

- 2026-05-11: CR authored retrospectively. Phase 17 scope triage Stage 2 bulk processing.
