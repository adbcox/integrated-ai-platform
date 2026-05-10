---
cr: CR-17-002
title: Music arr-stack (Lidarr) escalated to Phase 18 media-ops
status: applied
source_phase: Phase-17
target_phase: Phase-18
discovered: 2026-05-11
applied: 2026-05-11
affected_deliverables: [D-17-87, D-17-98, D-17-100, D-17-102, D-17-112]
summary: 5 Lidarr deployment + operational deliverables retrospectively escalated to Phase 18 media-ops (local-music-stack-v1).
---

# CR-17-002: Music arr-stack escalation

## Summary

Original arr-stack scope under Phase 17 was movies/TV (Radarr,
Sonarr, Prowlarr, Sportarr). Music (Lidarr) is a distinct media
class. D-17-87 deployed Lidarr; remaining deliverables continue
Lidarr operational work (auth, full config, import failures, SABnzbd
category misconfiguration). This belongs to Phase 18 media-ops
grouping (operator's "local-music-stack-v1: Lidarr + Navidrome"
roadmap).

## Affected deliverables

| ID | Title | Status |
|---|---|---|
| D-17-87 | Lidarr deployment (arr-stack music component) | DONE |
| D-17-98 | Lidarr authentication configuration fix | IN PROGRESS |
| D-17-100 | Lidarr full operational configuration | IN PROGRESS |
| D-17-102 | Lidarr SABnzbd category misconfiguration | IN PROGRESS |
| D-17-112 | Lidarr import failure investigation + remediation | IN PROGRESS |

## Rationale

Phase 17 plan's arr-stack work (D-17-08 Sportarr, D-17-44 Buildarr,
D-17-46 Scraparr metrics) targeted existing media classes the
platform already supported. Music was not a Phase 17 scope item —
Lidarr deployment is the introduction of a new media class with its
own deployment + config + ops surface.

The work landed under Phase 17 IDs because the CR-escalation
mechanism wasn't enforced. Retrospective escalation maps the work to
the correct Phase 18 §18.L media-ops grouping.

## Disposition

- All 5 deliverables retain their `D-17-NN` IDs.
- Intrinsic status preserved (1 DONE + 4 IN PROGRESS).
- Phase grouping moves to Phase 18 media-ops (Navidrome sibling).
- §9 rows gain `→ ESCALATED-TO-PHASE-18 via CR-17-002 (2026-05-11)` annotation.
- Phase 17 closeout criteria do NOT block on these deliverables.

## Cross-references

- Sibling CR: `CR-17-003` (arr-stack expansion + observability — overlapping §18.G/§18.L scope).
- Sibling CR: `CR-17-006` (misc Phase-18 — D-17-76 seedbox bootstrap is §18.L companion).
- Roadmap (user-memory): local-music-stack-v1 — Lidarr + Navidrome.

## Audit trail

- 2026-05-11: CR authored retrospectively. Phase 17 scope triage Stage 2 bulk processing.
