# RM-MEDIA-002

- **ID:** `RM-MEDIA-002`
- **Title:** Unified media acquisition and watchlist automation system for Sonarr and Radarr
- **Category:** `MEDIA`
- **Type:** `Feature`
- **Status:** `In progress`
- **Maturity:** `M2`
- **Priority:** `High`
- **Priority class:** `P3`
- **Queue rank:** `2`
- **Target horizon:** `later`
- **LOE:** `L`
- **Strategic value:** `4`
- **Architecture fit:** `5`
- **Execution risk:** `2`
- **Dependency burden:** `3`
- **Readiness:** `near`

## Description
Build a unified media acquisition orchestration system that lets users request TV series and movies from the dashboard and automatically routes supported watchlist and wanted-list events into Sonarr and Radarr.

This item must be implemented **reuse-first**.
It is not permission to build a broad custom request portal, custom watchlist sync platform, or raw API wrapper layer from scratch when mature products and libraries already exist in the Plex and Arr ecosystem.

## Why it matters
Creates a high-utility household-facing workflow while leveraging established external media systems instead of rebuilding them.

It is also one of the clearest places where the platform can save time and token budget by modifying or wrapping mature OSS instead of writing broad greenfield media automation code.

## Governing reuse sources
This item is governed by:
- `docs/architecture/MEDIA_AUTOMATION_REUSE_REGISTER.md`
- `docs/roadmap/MEDIA_REUSE_IMPLEMENTATION_WAVE.md`
- `docs/roadmap/EXTERNAL_APPLICATIONS_AND_INTEGRATIONS.md`

## Key requirements
- manual request path
- watchlist-driven automation path
- Sonarr and Radarr routing
- duplicate detection and status feedback
- bounded service ownership and product-role clarity
- avoid unnecessary custom API wrappers where standard libraries already exist

### Preferred role owners now in scope
- **Plex** — media server and watchlist source
- **Sonarr** — TV acquisition and series automation
- **Radarr** — movie acquisition and library automation
- **Prowlarr** — indexer management
- **Overseerr** — request portal candidate
- **PyArr** — primary low-level Arr automation library
- **PlexAPI** — primary low-level Plex automation library
- **ArrAPI** — selective lighter library when simple web-client-like interaction is preferable

### Watchlist-sync evaluation lane now in scope
Choose one primary pattern to evaluate first from:
- **Fetcharr**
- **Watchlistarr**
- **Pulsarr**

Do not treat all of them as co-primary owners of the same role.

### Product reuse now in scope
Use or wrap before rebuilding:
- **Overseerr** for request portal and approval flows
- **Maintainerr** for maintenance and cleanup rules where lifecycle management overlaps this branch
- **Kometa** for metadata, collections, overlays, and discoverability support where relevant to media branch UX

### Selective references now in scope
- **Homarr** for dashboard and status aggregation reference patterns
- **Plex Autoscan** patterns for targeted scan optimization
- **syncarr** for multi-instance Arr sync patterns if multi-instance routing becomes necessary

## Affected systems
- media branch
- dashboard and control surfaces
- external media automation integrations
- watchlist and request orchestration surfaces
- future maintenance and metadata-adjacent media surfaces

## Expected file families
- future media orchestration/adapters
- future dashboard request/status surfaces
- future media wrapper scripts and thin integration layers
- future deployment notes and config templates for selected media systems

## Dependencies
- external documentation packs for Sonarr, Radarr, Plex, and request flows
- `RM-MEDIA-001`
- `RM-GOV-009`

## Risks and issues
### Key risks
- title ambiguity and backend coupling
- adopting too many overlapping media products for the same role
- writing custom watchlist or request logic where mature products already exist

### Known issues and blockers
- exact watchlist integration posture must remain bounded and documented
- one primary watchlist-sync pattern should be chosen before broad custom sync work begins
- product ownership boundaries should remain explicit

## CMDB / asset linkage
- should later remain linkable to media services and endpoint environment
- should align with media endpoint and service inventory truth

## Grouping candidates
- `RM-MEDIA-001`

## Grouped execution notes
- Shared-touch rationale: media orchestration, endpoint/media-service context, request flows, and watchlist automation overlap strongly.
- Repeated-touch reduction estimate: high.
- Grouping recommendation: `Bundle now`

## Recommended first milestone
Complete the first media reuse wave:
- PyArr
- PlexAPI
- Overseerr
- choose one primary watchlist-sync candidate
- define how request and watchlist flows surface status back into the governed dashboard/control layer

## Status transition notes
- Expected next status: `Decomposing`
- Transition condition: supported request and watchlist path, product-role ownership, library reuse posture, and first media reuse wave are explicitly defined
- Validation and closeout condition: one bounded acquisition workflow functions end to end with clear status handling and assistants no longer need to re-derive whether to build these media subsystems from scratch

## Notes
This item is the canonical roadmap home for reuse-first media acquisition and watchlist automation on top of Plex and the Arr ecosystem.