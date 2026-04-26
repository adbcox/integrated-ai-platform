# Media Stack Audit

Audit of existing media infrastructure vs roadmap items. Performed 2026-04-24.

## Services

| Service | Host | Port | Status | Auth Required |
|---------|------|------|--------|---------------|
| Sonarr | 192.168.10.201 (QNAP) | 8989 | **Reachable** | API key needed for data |
| Radarr | 192.168.10.201 (QNAP) | 7878 | **Not reachable** (connection refused) | — |
| Prowlarr | 192.168.10.201 (QNAP) | 9696 | **Not reachable** (connection refused) | — |
| Plex | mac-mini.local | 32400 | Not reachable (not yet installed) | Token needed |

> Note: The earlier `curl` tests showed Sonarr/Radarr/Prowlarr as reachable because the pipeline exit code came from `head -5` (always 0), not from curl's `-f` flag. Direct Python requests confirmed Radarr and Prowlarr are not accessible from this host at those ports.

## Code Inventory (as of audit)

### Built and functional

| File | What it does |
|------|-------------|
| `connectors/arr_stack.py` | ArrStackConnector — health_check, queue, calendar, series count, movie count, indexer count |
| `connectors/plex.py` | PlexConnector — health_check, server_info, active_sessions, library_stats (**new**) |
| `connectors/home_assistant.py` | HomeAssistantConnector — not media-related |
| `domains/media.py` | MediaDomain — health_check + get_stats() + get_upcoming() with API key wiring (**enhanced**) |
| `config/connectors.yaml` | arr_stack and plex connector config with env var references |
| `config/homepage/services.yaml` | Media group: Plex, Sonarr, Radarr, Prowlarr + Media Stats widget (**updated URLs**) |
| `web/dashboard/server.py` | GET /api/media/status endpoint (**new**) |

### Gaps requiring action

1. **API keys not configured** — Add keys to `docker/.env` (copy from `.env.example`):
   - `SONARR_API_KEY` — find in Sonarr → Settings → General → API Key
   - `RADARR_API_KEY` — find in Radarr → Settings → General → API Key  
   - `PROWLARR_API_KEY` — find in Prowlarr → Settings → General → API Key
   - `PLEX_TOKEN` — find via Plex web UI → Account → XML or use `PlexAPI` to generate

2. **Radarr/Prowlarr not reachable** — Verify ports. They may be on different ports or require VPN/LAN access that isn't active in this session.

3. **Plex not installed on Mac Mini** — Homepage config points to mac-mini.local:32400; Plex needs to be installed or the URL updated to its actual host.

## Roadmap Items Status

| ID | Title | Status | Action |
|----|-------|--------|--------|
| RM-MEDIA-001 | Endpoint health + Plex compliance | Completed | Foundation wired |
| RM-MEDIA-002 | Watchlist automation (Sonarr/Radarr) | Completed | PyArr/PlexAPI to wire |
| RM-MEDIA-003 | Inventory hygiene + duplicate detection | Completed | — |
| RM-MEDIA-004 | Config optimization + sports acquisition | Completed | — |
| RM-MEDIA-005 | Backlog placeholder | Retired | — |
| RM-MEDIA-006 | Enhancement, restoration, tagging | Completed | Video2X/YOLO/FiftyOne scope |
| RM-MEDIA-010 | Video transcoding (FFmpeg) | Completed | — |
| RM-MEDIA-011 | Audio transcription (Whisper) | Completed | — |
| RM-MEDIA-012 | Image optimization + CDN | In progress | — |
| RM-MEDIA-013 | Streaming infrastructure (HLS/DASH) | In progress | — |
| RM-MEDIA-014 | Metadata extraction + tagging | In progress | — |
| RM-MEDIA-015 | Thumbnail generation | Accepted | — |
| RM-MEDIA-016 | Video quality analysis + encoding | In progress | — |
| RM-MEDIA-017 | Audio normalization | Accepted | — |
| RM-MEDIA-018 | Storage optimization | Accepted | — |
| RM-MEDIA-019 | Real-time processing queue | Accepted | — |
| RM-MEDIA-020 | Format conversion API | Accepted | — |
| RM-MEDIA-021 | Subtitle generation + sync | Accepted | — |
| RM-MEDIA-022 | Analytics + usage tracking | Accepted | — |
| RM-MEDIA-023 | CDN integration | Accepted | — |
| RM-MEDIA-024 | Backup + disaster recovery | Accepted | — |

## Priority Next Steps

1. **Get API keys** — Without them, `get_stats()` shows zeros. Takes 5 minutes.
2. **Verify Radarr/Prowlarr** — Check actual running ports on QNAP. Possibly 7878 is mapped differently.
3. **Install Plex** on Mac Mini or update Plex URL in `config/homepage/services.yaml` and `config/domains.yaml`.
4. **Set up Overseerr** (RM-MEDIA-002) — Request portal that bridges Plex watchlist → Sonarr/Radarr.

## Dashboard Integration

Live media stats available at:
- **`GET /api/media/status`** — `http://mac-mini.local:8080/api/media/status`

Returns: Sonarr series counts, Radarr movie counts, Prowlarr indexer status, Plex active streams.

Homepage "Media Stats" widget is configured to pull from this endpoint automatically.
