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

**2026-05-04 hygiene refresh** — gate predicate corrected per D-17-76
audit. The prior framing said Seeker enablement was gated on
download-client credentials; that was wrong. Cleanuparr's *Seeker*
module hunts via Sonarr/Radarr APIs (already rendered into the cleanuparr
sidecar via `secret/arr/sonarr` + `secret/arr/radarr`) and does NOT talk
to download clients directly. Only Cleanuparr's *Cleaner* modules need
download-client API access.

**Scope correction:** the only torrent client in scope is the
seedbox-resident qBittorrent WebUI. SABnzbd is NOT in the platform stack
(legacy/inert); QNAP qBittorrent is similarly out of scope. The credential
target is `secret/seedbox/qbittorrent` (D-17-76), not the previously-named
`secret/downloads/qbittorrent` / `secret/downloads/sabnzbd` paths.

Closure-DONE blockers (revised):

1. Operator completes UI setup wizard (currently `/api/v1/health`
   returns `{"error":"Setup required"}`). Procedure:
   `docs/runbooks/cleanuparr-first-run.md` Section 1.
2. Operator authorizes Seeker first-pass enablement (UI flip from
   `search_enabled=0` to enabled, with `dry_run=1` retained for one
   cycle). Procedure: `docs/runbooks/cleanuparr-first-run.md` Section 2.
3. `secret/seedbox/qbittorrent` populated via
   `scripts/provision-seedbox-credentials.sh` (D-17-76 substrate, landed
   at `c04c760`). **Cleaner-modules-only gate** — does NOT block Seeker.
4. D-17-76 commit-2 lands (cleanuparr policy extension + sidecar template
   `QBIT_*` block + provision-cleanuparr conditional readback). Blocked
   on (3); M3 ordering avoids template render-failure foot-gun.
5. Operator authorizes Cleaner module enablement (separate decision
   after Seeker first-real-search cycle observed clean).
