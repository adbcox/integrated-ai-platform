# ADR-A-009: Vault as Authoritative Secret Store — Migration from .env

**Status:** Accepted  
**Date:** 2026-04-27  
**Deciders:** Adrian Cox

---

## Context

Prior to Phase 16, secrets were stored in two places:
- Vault (server mode, Shamir 5-of-3): 14 paths covering Arr stack, Nextcloud, Vaultwarden, Zabbix, MinIO backup, Restic, Strava OAuth, OPNsense, QNAP SNMP
- `docker/.env` (git-ignored): 20+ secrets including PLEX_TOKEN, GITHUB_TOKEN, HA_TOKEN, PLANE credentials, OBOT_ADMIN_PASSWORD, SEEDBOX_PASSWORD, QNAP_PASS — **not in Vault**

Additionally:
- `docker/nextcloud/.env`, `docker/vaultwarden/.env`, `docker/zabbix/.env` held plaintext secrets that Vault also stored — Vault copies were out-of-band documentation only
- `secret/seedbox` path was empty (no fields)
- `secret/strava/oauth` had `refresh_token="n/a"` and `access_token="n/a"` (OAuth never completed)

## Decision

1. **Vault is the single source of truth for all secrets.** `.env` files are generated from Vault at deploy time and are never committed.

2. **`vault-mapping.yaml` per stack** maps `ENV_VAR_NAME: secret/path:field`. This file IS committed — it contains no secrets, only paths.

3. **`scripts/lib/vault-generate-env.py`** reads a mapping file and pulls values from Vault via `docker exec`. Used by `scripts/deploy-stack.sh`.

4. **`docker/.env`** retains static non-secret config (URLs, ports, TZ, PUID) and is populated with Vault-sourced secrets at deploy time. The file format is preserved so existing compose files work without modification.

5. **Corrupted Vault entries cleaned:**
   - `secret/seedbox` (empty) — deleted; replaced with `secret/seedbox/account` with actual password
   - `secret/strava/oauth` (n/a values) — deleted; replaced with proper structure. `access_token` and `refresh_token` remain `PENDING_OAUTH` until OAuth authorization grant is completed.

6. **New Vault paths created:**
   - `secret/plex/api` — token, homepage_token
   - `secret/qnap/admin` — password
   - `secret/seedbox/account` — password
   - `secret/github/api` — token
   - `secret/plane/api` — token
   - `secret/plane/admin` — password
   - `secret/plane/app` — secret_key
   - `secret/plane/minio` — username, password
   - `secret/obot/admin` — password
   - `secret/homeassistant/api` — token, homepage_token
   - `secret/openweathermap/api` — key

## Consequences

**Positive:**
- All secrets now have a single authoritative location
- Secret rotation can be done in Vault without editing .env files
- `.env` files committed to git (accidentally) would contain only non-secret config

**Negative / Known Gaps:**
- `docker/nextcloud/.env`, `docker/vaultwarden/.env`, `docker/zabbix/.env` still contain plaintext credentials — the compose files read from `.env` at startup, not from Vault at runtime. Vault Agent sidecar injection would fix this but adds complexity. Accepted as a known gap: Vault holds the canonical copy; rotation requires regenerating `.env` and restarting the stack.
- Strava OAuth requires a one-time browser action to complete the authorization grant. No automation is possible for this step.
- `secret/arr/*` URLs use `mac-mini.internal` (Unbound hostname) — if Unbound stops, lookups break.

## Vault Path Reference

See `docker/vault-mapping.yaml` for the complete ENV → Vault path mapping.

## Backup

Phase 16 backup at: `backups/phase16-20260427-172029/` (gitignored)
- `vault-state-before.txt` — snapshot of all Vault paths before migration
- `docker/.env` — original .env backup
