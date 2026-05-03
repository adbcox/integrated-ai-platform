# ADR-A-006 — Repo docs are canonical for architecture and roadmap planning
**Status:** Accepted (path claims updated 2026-05-03 by D-17-16; Plane CE consequences superseded by OpenProject migration in D-17-04)
**Date:** 2026-04-25
**Source:** docs/DECISION_REGISTER.md (path corrected — `docs/architecture/DECISION_REGISTER.md` was a stale filing convention; never moved)

## Context

Multiple external tools (Plane, Notion, Confluence) can hold documentation. There was risk of the canonical source of truth fragmenting across systems, with no single authoritative location for architecture decisions and roadmap planning.

## Decision

Repo-owned docs remain canonical for architecture and roadmap planning. Tools such as Plane are operational overlays rather than the planning source of truth.

## Consequences

- `docs/architecture-facts/` is authoritative for per-subsystem architecture chronicles (post-D-17-16; absorbed `docs/architecture/`)
- `docs/PHASE_ROADMAP.md` + `docs/PROJECT_FRAMEWORK.md` §9 are authoritative for roadmap + deliverable definitions (post-D-17-04 OpenProject migration; old `docs/roadmap/ITEMS/` retired)
- OpenProject (post-D-17-04) holds operational state (issue status, assignments) but not the definition; Plane CE (the original consequence target) was retired in WP-17-04-06 (`726725a`)
- Notion, Confluence, and similar tools are overlays — useful for collaboration but not canonical
- One-way sync `scripts/openproject-sync-from-framework.py` pushes FROM repo TO OpenProject, not the reverse (was `sync_roadmap_to_plane.py` pre-D-17-04)
- This ADR is the reason `docs/adr/` is a protected path in CODEOWNERS
- External knowledge tools (AnythingLLM, etc.) ingest FROM this repo — this repo is the source
