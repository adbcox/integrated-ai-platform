# D-17-49 — Cleanuparr Seeker-Consolidated Deployment Smoke

Date: 2026-05-03

## Runtime state

- `cleanuparr` deployed in arr-stack and healthy on `:11011`.
- Caddy route active: `cleanuparr.internal` -> `host.docker.internal:11011`.
- Huntarr removed from active deployment after upstream image unavailability.
- Huntarr scaffolding preserved under:
  `docker/_deferred/huntarr-upstream-unreachable-2026-05-03/`.

## Safety posture (WP-07 operator-approved)

- `dry_run=1` (global dry-run enabled).
- Queue Cleaner disabled.
- Download Cleaner disabled.
- Seeker global search disabled (`search_enabled=0`).

## Seeker staged (not enabled)

- Sonarr + Radarr instances configured via container DNS:
  - `http://sonarr:8989`
  - `http://radarr:7878`
- Conservative per-instance caps staged:
  - `active_download_limit=2`
  - `min_cycle_time_days=3`
  - `monitored_only=1`
  - cutoff/custom-format hunts disabled

## Gating dependencies (blocking closure)

- Vault paths not present:
  - `secret/downloads/qbittorrent`
  - `secret/downloads/sabnzbd`
- No empty scaffolds created by policy.
- Component remains DEPLOYED/observable and not closure-DONE until:
  1. §18.L populates download-client credentials,
  2. operator authorizes Seeker first-pass enablement.
