# Media Automation Reuse Register

## Purpose

This document defines the reuse-first adoption posture for the media automation branch of the integrated AI platform.

It exists to stop assistants from rebuilding broad Plex, Sonarr, Radarr, Prowlarr, request-management, metadata-management, and maintenance systems when mature OSS products and libraries already exist.

## Core rule

For media automation:
- prefer full products where the product already owns the role well
- prefer standard libraries for direct API control
- prefer thin wrappers over custom rebuilds
- prefer existing request, maintenance, metadata, and watchlist-sync systems before inventing weak first-pass equivalents

## Media reuse register

| System or library | Role | Reuse mode | What to reuse | Notes |
|---|---|---|---|---|
| Plex Media Server | media server backbone | adopt/integrate | server, playback, metadata base, watchlist surface | Core external media surface |
| Sonarr | TV acquisition and series automation | adopt/integrate | series management, queue, monitoring, upgrades | Core Arr role owner |
| Radarr | movie acquisition and library automation | adopt/integrate | movie management, queue, monitoring, upgrades | Core Arr role owner |
| Prowlarr | indexer and upstream Arr proxy | adopt/integrate | indexer management and distribution | Strong companion to Sonarr and Radarr |
| Overseerr | request portal and discovery UX | adopt-selective and wrap | request workflow, discovery portal, approval patterns | Strong request-management product |
| Homarr | dashboard and integration reference | adopt-selective and reference | dashboard patterns, widget integration, status aggregation ideas | Useful for UI patterns, not governance authority |
| Maintainerr | maintenance and deletion rule engine | adopt-selective and wrap | maintenance rules, deletion and cleanup workflows | Strong library maintenance product |
| Kometa | metadata, overlays, collections, posters | adopt-selective and wrap | metadata automation, collection generation, overlays, config patterns | Strong metadata and collections owner |
| Fetcharr, Watchlistarr, Pulsarr | watchlist sync and watchlist-triggered acquisition | selective adopt and reference | Plex watchlist sync flows, webhook and sync patterns, routing ideas | Choose one primary pattern, not many |
| PyArr | Python Arr API wrapper | reuse as library | direct Sonarr, Radarr, Prowlarr automation scripts and services | Good low-level Python automation layer |
| ArrAPI | lightweight Sonarr and Radarr Python wrapper | reuse as library selectively | simple web-client-like interaction patterns | Lighter alternative to PyArr |
| PlexAPI | deep Plex Python control library | reuse as library | library inspection, metadata, playback control, watchlist/account access | Strong unofficial Python standard |
| Plex Autoscan | webhook-triggered targeted scans | adopt-selective and reference | webhook-driven scan optimization patterns | Good targeted scan optimization reference |
| syncarr | multi-instance Arr sync | adopt-selective and reference | one-way or two-way multi-instance sync patterns | Strong for 4K and 1080p or multi-instance sync scenarios |

## Preferred ownership by role

### Core media operations
- Plex
- Sonarr
- Radarr
- Prowlarr

### Request management
- Overseerr

### Metadata and collections
- Kometa

### Maintenance and cleanup
- Maintainerr

### Watchlist-driven automation
Choose one primary pattern from:
- Fetcharr
- Watchlistarr
- Pulsarr

### Low-level automation libraries
Primary Python libraries:
- PyArr
- PlexAPI

Selective lighter library:
- ArrAPI

## Assistant rules

1. Pick a role owner first.
2. Prefer mature product plus thin wrapper.
3. Use libraries for custom glue, not full rewrites.
4. Avoid duplicate watchlist systems.
5. Keep governance local.

## Recommended first-wave media reuse targets

1. PyArr
2. PlexAPI
3. Overseerr
4. Maintainerr
5. Kometa
6. one watchlist-sync product
7. Plex Autoscan patterns if scan efficiency becomes a bottleneck

## Relationship to roadmap

This document is especially relevant to:
- RM-MEDIA-001
- RM-GOV-009
- RM-OPS-006

## Notes

This register is intended to make the media branch reuse-first by default.