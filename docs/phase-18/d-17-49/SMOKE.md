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

**2026-05-04 third hygiene refresh** — four errors corrected:

1. **API namespace error** — earlier framing relied on a probe of
   `/api/v1/health` that returned `{"error":"Setup required"}`. That
   path is **not a real Cleanuparr endpoint**; the API is `/api/*`
   (no `v1` prefix). The actual setup-status probe is
   `GET /api/auth/status` → `{"setupCompleted":true,...}`. The setup
   wizard was already complete at deploy. **Setup-wizard gate did not
   exist.**

2. **Wrong download client identification (platform side)** — earlier
   framing assumed qBittorrent for the seedbox. The seedbox
   (`5.nl19.seedit4.me`, `seedit4me`) actually runs **rTorrent**
   (torrent client, XML-RPC API) + **SABnzbd** (Usenet client, REST API
   with api_key). Both are platform-canonical; both are seedbox-resident.
   Verified via `connectors/seedbox.py`,
   `docs/runbooks/syncthing-rebuild.md`,
   `docs/adr/ADR-A-007-media-sync-syncthing.md`.

3. **Operator-UI premise wrong** — Cleanuparr is fully API-driven
   (compiled SPA enumerated routes; config persists in SQLite at
   `/config/cleanuparr.db`; `/api/configuration/*` PUT endpoints accept
   full posture as JSON). All Seeker/Cleaner enablement is scriptable.
   The earlier `cleanuparr-first-run.md` (UI walkthrough) is discarded.

4. **Cleanuparr does not support SABnzbd** (image-binary verified
   2026-05-04). Live API probe of
   `POST /api/configuration/download_client/` against the deployed
   `ghcr.io/cleanuparr/cleanuparr:latest` rejects every Usenet/SAB
   `typeName` value; binary `strings` of `/app/Cleanuparr` (207 MB)
   returns a single occurrence of "Usenet" (a category enum label) and
   **zero** occurrences of "Sabnzbd" / "SABnzbd" / "nzbget". The
   compiled SPA bundle in `/app/wwwroot` is also negative for those
   tokens. The `DownloadClientTypeName` enum in this build is
   torrent-only: `{ Deluge, Transmission, rTorrent, uTorrent,
   qBittorrent }`. Implication: **Cleanuparr Cleaner coverage is
   rTorrent-only on this platform**; SABnzbd queue/download cleaning is
   a documented coverage gap (known limitation), not an implementation
   bug.

**Revised closure plan — Cleanuparr scoped to rTorrent only; SABnzbd retained as platform-canonical Usenet client outside Cleanuparr scope:**

1. Strip qBittorrent → rTorrent + SABnzbd across Vault substrate
   (vault-mapping, seedbox-policy, provision script, SMOKE.md, framework
   rows). Both Vault paths (`secret/seedbox/rtorrent` + `secret/seedbox/sabnzbd`)
   are provisioned because SABnzbd is platform-canonical; future
   non-Cleanuparr consumers (Sonarr/Radarr direct, queue-monitor sidecar,
   etc.) read SABnzbd creds from Vault. Cleanuparr does NOT.
2. Operator runs `scripts/provision-seedbox-credentials.sh` to populate
   `secret/seedbox/rtorrent` + `secret/seedbox/sabnzbd` (interactive
   credential entry — terminal only, no UI).
3. `scripts/cleanuparr-api.sh` (X-Api-Key wrapper around curl) +
   `scripts/cleanuparr-bootstrap-config.sh` (POST `/api/configuration/download_client/`
   for **rTorrent only**; PUT `/api/configuration/seeker` to set
   `searchEnabled: true` with conservative per-instance caps; Cleaner
   modules staged disabled; `--enable-cleaners` flag for post-Seeker
   observation flip).
4. `secret/cleanuparr/api:key` Vault-stored from running container's
   SQLite (one-time hash-only extract + write per F6 doctrine).
5. D-17-76 commit-2 extends `config/vault-policies/cleanuparr-policy.hcl`
   with `secret/data/seedbox/rtorrent` + `secret/data/cleanuparr/api`
   read paths, and `docker/vault-agent-cleanuparr/credentials.env.tmpl`
   with `RTORRENT_*` + `CLEANUPARR_API_KEY` blocks. **No `SABNZBD_*`
   block in cleanuparr sidecar** — Cleanuparr never reads SABnzbd creds.
6. After Seeker first-real-search cycle observed clean, operator runs
   `scripts/cleanuparr-bootstrap-config.sh --enable-cleaners` to flip
   Cleaner modules on (rTorrent-side only).

The only operator action is step 2 (credential entry) and the cycle
authorization in step 6 — both terminal-only, no UI session.

## Known limitation — Cleanuparr SABnzbd coverage gap

Cleanuparr does not implement SABnzbd as a download-client type in the
deployed image (`ghcr.io/cleanuparr/cleanuparr:latest`, binary
verified 2026-05-04). Implications:

- **rTorrent traffic** (torrent half of seedbox throughput) is covered
  by Cleanuparr Seeker + Queue/Download Cleaners after Cleaner enable.
- **SABnzbd traffic** (Usenet half) is **not** covered by Cleanuparr.
  Stuck/stalled NZB downloads, blocked-import remediation, and stalled-
  download tagging on the Usenet path remain on Sonarr/Radarr's own
  built-in handling and operator manual intervention.
- SABnzbd Vault credentials (`secret/seedbox/sabnzbd`) are still
  provisioned because SABnzbd is platform-canonical and other consumers
  (Sonarr/Radarr direct config, future queue-monitor sidecars) need
  them. Cleanuparr's Vault Agent sidecar simply does not render them.
- Coverage gap closure is a future deliverable (upstream Cleanuparr
  SABnzbd support OR a sibling sabnzbd-arr-style standalone cleaner OR
  Sonarr/Radarr-side queue-stall remediation). Not blocking D-17-49
  closure.
