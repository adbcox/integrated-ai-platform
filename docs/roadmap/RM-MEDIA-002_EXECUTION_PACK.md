# RM-MEDIA-002 — Execution Pack

## Title

**RM-MEDIA-002 — Unified media acquisition and watchlist automation system for Sonarr and Radarr**

## Canonical relationship

- Master roadmap authority: `docs/roadmap/ROADMAP_MASTER.md`
- Normalized backlog entry: `docs/roadmap/ROADMAP_INDEX.md`
- Related items: `RM-MEDIA-001`, `RM-MEDIA-004`

## Objective

Unify media request/watchlist intent and acquisition flows for Sonarr and Radarr under one controlled media-management system.

## Why this matters

This is the core automation layer for TV/movie acquisition and request routing in the media-control branch.

## Required outcome

- unified request/watchlist model
- Sonarr/Radarr routing logic
- acquisition status visibility
- controlled automation flow into library organization

## Recommended posture

- keep this in the media-control branch, not as a separate architecture
- separate request intent, acquisition state, and library outcome
- preserve reviewability of routing rules

## Required artifacts

- request/watchlist schema
- routing decision record
- acquisition state record
- library handoff/status record

## Best practices

- distinguish movie versus episodic routing clearly
- preserve source of request intent
- maintain traceability from request to acquisition outcome
- keep routing rules explicit and machine-readable

## Common failure modes

- watchlist automation with no clear routing logic
- weak visibility into acquisition state
- media requests that disappear into the stack with no traceability
- coupling request logic too tightly to one downstream tool instance

## Recommended first milestone

Define the request/watchlist schema and routing decision model first, then wire bounded Sonarr/Radarr automation flows.
