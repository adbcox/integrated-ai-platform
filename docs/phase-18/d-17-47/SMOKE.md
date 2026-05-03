# D-17-47 — Bazarr Subtitle Automation Smoke

Date: 2026-05-03

## WP-03 deployment checks

- `bazarr` container up and `healthy` on `0.0.0.0:6767`.
- Direct UI probe: `http://localhost:6767` -> `200`.
- Caddy route loaded for `bazarr.internal` (local resolve probe via
  `--resolve bazarr.internal:443:127.0.0.1` -> `200`).
- LAN DNS resolution for `bazarr.internal` requires operator-side
  Unbound host override per runbook:
  `docs/runbooks/opnsense-add-host-overrides.md`.

## WP-04 integration checks

- Bazarr configured for Sonarr/Radarr via container DNS:
  - `http://sonarr:8989`
  - `http://radarr:7878`
- Vault Agent sidecar rendered Bazarr credentials file:
  `/Users/admin/.vault-agent-secrets/bazarr/credentials.env`
- Hash-only verification:
  - Sonarr API key sha256[12]: `cde8de07c824`
  - Radarr API key sha256[12]: `cfd54d7fba5f`

## WP-05 provider gate

- Enabled no-credential baseline providers only:
  `embeddedsubtitles`, `napiprojekt`, `podnapisi`, `subf2m`,
  `animetosho`.
- Deferred providers requiring account/API key:
  `opensubtitlescom`, `addic7ed`, `subdl`, regional/account-bound
  providers. Tracked in `PHASE_ROADMAP.md` §18.L queue.

## WP-06 test cycle

- Bazarr API smoke:
  `PATCH /api/episodes/subtitles` returned `204` for live Sonarr episode
  (`seriesid=48`, `episodeid=2669`).
- Selected sample episode had `missing_subtitles=[]`, so no new external
  subtitle sidecar file was emitted in that specific run.
