# ADR-A-006 — Repo docs are canonical for architecture and roadmap planning
**Status:** Accepted
**Date:** 2026-04-25
**Source:** docs/architecture/DECISION_REGISTER.md

## Context

Multiple external tools (Plane, Notion, Confluence) can hold documentation. There was risk of the canonical source of truth fragmenting across systems, with no single authoritative location for architecture decisions and roadmap planning.

## Decision

Repo-owned docs remain canonical for architecture and roadmap planning. Tools such as Plane are operational overlays rather than the planning source of truth.

## Consequences

- `docs/architecture/` is authoritative for all architecture decisions
- `docs/roadmap/ITEMS/` is authoritative for roadmap item definitions
- Plane CE holds operational state (issue status, assignments) but not the definition
- Notion, Confluence, and similar tools are overlays — useful for collaboration but not canonical
- Bidirectional sync scripts (sync_roadmap_to_plane.py) push FROM repo TO Plane, not the reverse
- This ADR is the reason `docs/adr/` is a protected path in CODEOWNERS
- External knowledge tools (AnythingLLM, etc.) ingest FROM this repo — this repo is the source
