# FlareSolverr — QNAP Container Station retirement

**Status:** 7-day cooldown — DO NOT delete before 2026-05-11
**Retired:** 2026-05-04 (D-17-108)
**Migration target:** Mac Mini Docker arr-stack (`flaresolverr` container)

## Source state at migration

| Field | Value |
|---|---|
| Host | QNAP NAS (192.168.10.201) |
| Runtime | QNAP Container Station (dockerd, no CLI on SSH path) |
| Container hostname | `cdff03c5564a` |
| Image | `ghcr.io/flaresolverr/flaresolverr:latest` |
| Version | 3.4.6 (confirmed via `/v1` API) |
| Port binding | `0.0.0.0:8191 → container:8191` |
| Env vars | Defaults only (LOG_LEVEL not set, no CAPTCHA_SOLVER) |
| Persistent sessions | 0 |
| Restart policy | Container Station managed |
| Process | PID 6317 dumb-init + PID 6447 python /app/flaresolverr.py |

## Why migrated

Architecture doctrine: application containers belong on Mac Mini Docker,
not QNAP Container Station. QNAP is the NAS (downloads, media, backups).

Root cause of migration trigger (D-17-107): Prowlarr container
(172.23.0.12 on control-center-net) got TCP RST from QNAP:8191 due to
QNAP QTS packet-filtering blocking Docker bridge subnet source IPs.
Same pattern as Syncthing port 8384 (D-17-105).

## Decommission steps

1. [ ] 2026-05-11 — Stop QNAP Container Station FlareSolverr container via QNAP web UI (Container Station → Containers → FlareSolverr → Stop)
2. [ ] 2026-05-11 — Delete container (Container Station → Containers → FlareSolverr → Remove)
3. [ ] Optionally remove image to free QNAP disk

## Mac Mini replacement verified working

- Container `flaresolverr` on `control-center-net`
- `docker exec prowlarr curl -X POST http://flaresolverr:8191/v1 -d '{"cmd":"sessions.list"}'` → `{"status":"ok","version":"3.4.6"}`
- Prowlarr proxy URL updated: `http://192.168.10.201:8191/` → `http://flaresolverr:8191/`
- `IndexerProxyStatusCheck` health issue cleared after proxy URL update
