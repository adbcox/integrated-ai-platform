# Infrastructure Audit Report
Date: 2026-04-27

---

## 1. VAULT STATE — COMPLETE INVENTORY

### Paths that exist (`secret/`)

| Vault Path | Fields Present | Notes |
|-----------|---------------|-------|
| `secret/arr/prowlarr` | api_key, url | url uses `mac-mini.internal` (old hostname format) |
| `secret/arr/radarr` | api_key, url | url uses `mac-mini.internal` |
| `secret/arr/sonarr` | api_key, url | url uses `mac-mini.internal` |
| `secret/headscale/admin` | preauth_key, server_url | preauth_key is valid |
| `secret/minio/backup` | access_key, endpoint, secret_key | functional |
| `secret/nextcloud/admin` | password, url, username | functional |
| `secret/nextcloud/db` | password | functional |
| `secret/opnsense/api` | api_key, api_secret, host | functional |
| `secret/opnsense/snmp` | community, host | functional |
| `secret/qnap/snmp` | community, host, version | functional |
| `secret/restic/backup` | password | functional |
| `secret/seedbox` | (empty — no fields) | **EMPTY** |
| `secret/strava/oauth` | access_token=n/a, client_id, client_secret, note, refresh_token=n/a | **INCOMPLETE — both tokens are literal "n/a"** |
| `secret/vaultwarden/admin` | token, url | functional |
| `secret/zabbix/admin` | password, url, username | functional |

### Paths that do NOT exist but are referenced

| Referenced Path | Referenced By | Status |
|----------------|--------------|--------|
| `secret/mcp/strava` | user instruction (today) | Does not exist |

---

## 2. ARCHITECTURAL VIOLATIONS — SECRETS IN .env NOT IN VAULT

The platform decision is: all secrets live in Vault; `.env` files reference Vault or contain only non-secret config.

### `docker/.env` — Secrets that should be in Vault but aren't:

| Field in .env | In Vault? | Notes |
|--------------|-----------|-------|
| `SONARR_API_KEY` | ✅ `secret/arr/sonarr.api_key` | Duplicate — .env and Vault both have it |
| `RADARR_API_KEY` | ✅ `secret/arr/radarr.api_key` | Duplicate |
| `PROWLARR_API_KEY` | ✅ `secret/arr/prowlarr.api_key` | Duplicate |
| `PLEX_TOKEN` | ❌ Not in Vault | Only in .env |
| `QNAP_PASS` | ❌ Not in Vault | Only in .env (value: +Huckbear17) |
| `SEEDBOX_PASSWORD` | ❌ Not in Vault (secret/seedbox is empty) | Only in .env |
| `HOMEPAGE_VAR_HASS_TOKEN` | ❌ Not in Vault | Only in .env |
| `HOMEPAGE_VAR_PLEX_TOKEN` | ❌ Not in Vault | Same as PLEX_TOKEN |
| `HOMEPAGE_VAR_SONARR_KEY` | ✅ Duplicate of SONARR | |
| `HOMEPAGE_VAR_RADARR_KEY` | ✅ Duplicate of RADARR | |
| `HOMEPAGE_VAR_PROWLARR_KEY` | ✅ Duplicate of PROWLARR | |
| `HOMEPAGE_VAR_PORTAINER_KEY` | ❌ Not in Vault | Portainer not in registry |
| `HOMEPAGE_VAR_OWM_KEY` | ❌ Not in Vault | OpenWeatherMap key |
| `PLANE_SECRET_KEY` | ❌ Not in Vault | Plane internal signing key |
| `PLANE_ADMIN_PASSWORD` | ❌ Not in Vault | |
| `PLANE_API_TOKEN` | ❌ Not in Vault | |
| `MINIO_ROOT_PASSWORD` | ❌ Not in Vault (secret/minio/backup has Plane MinIO, not this) | docker/.env MinIO = Plane's internal MinIO |
| `OBOT_ADMIN_PASSWORD` | ❌ Not in Vault | |
| `GITHUB_TOKEN` | ❌ Not in Vault | |
| `STRAVA_CLIENT_SECRET` | ✅ `secret/strava/oauth.client_secret` | |
| `STRAVA_ACCESS_TOKEN` | ✅ `secret/strava/oauth.access_token` (value=n/a) | Token in .env is expired; n/a in Vault |
| `HA_TOKEN` | ❌ Not in Vault | Home Assistant long-lived token |

### `docker/nextcloud/.env` — Violates Vault policy:
Both `NEXTCLOUD_DB_PASSWORD` and `NEXTCLOUD_ADMIN_PASSWORD` are stored in plaintext here AND in Vault. The compose file reads from `.env`, not Vault. This is a functional violation: Vault has the authoritative copy but services use the `.env` copy.

### `docker/vaultwarden/.env` — Violates Vault policy:
`ADMIN_TOKEN` in plaintext. Vault has a copy at `secret/vaultwarden/admin.token`.

### `docker/zabbix/.env` and `.env.zabbix-admin` — Violates Vault policy:
`POSTGRES_PASSWORD` and `ZABBIX_ADMIN_PASSWORD` in plaintext. Vault has admin creds at `secret/zabbix/admin`.

---

## 3. SCRIPT vs VAULT PATH MISMATCH MATRIX

| Script | Vault Path Referenced | Path Exists? | Field Available? |
|--------|-----------------------|-------------|-----------------|
| `backup.sh` | `secret/minio/backup.access_key` | ✅ | ✅ |
| `backup.sh` | `secret/minio/backup.secret_key` | ✅ | ✅ |
| `backup.sh` | `secret/restic/backup.password` | ✅ | ✅ |
| `refresh-strava-token.sh` | `secret/strava/oauth.refresh_token` | ✅ path | ❌ value is "n/a" |
| `refresh-strava-token.sh` | `secret/strava/oauth.client_id` | ✅ | ✅ |
| `refresh-strava-token.sh` | `secret/strava/oauth.client_secret` | ✅ | ✅ |
| `sync-strava-to-calendar.py` | `secret/strava/oauth.access_token` | ✅ path | ❌ value is "n/a" |
| `sync-strava-to-calendar.py` | `secret/nextcloud/admin.username` | ✅ | ✅ |
| `sync-strava-to-calendar.py` | `secret/nextcloud/admin.password` | ✅ | ✅ |

### Cron jobs that will FAIL at runtime:

| Cron | Script | Will it succeed? | Reason |
|------|--------|-----------------|--------|
| `0 2 * * *` | backup.sh | ✅ Yes | All Vault paths and fields exist |
| `*/30 * * * *` | refresh-strava-token.sh | ❌ No | refresh_token="n/a" — script will exit with "Refresh failed" |
| `0 6 * * *` | sync-strava-to-calendar.py | ❌ No | access_token="n/a" — Strava API will reject |

---

## 4. GIT HISTORY — filter-branch DAMAGE ASSESSMENT

- **refs/original/**: Empty directory — was cleaned up with `git reflog expire --expire=now && git gc --prune=now`
- **Recovery refs**: Reflog only goes back 4 commits (ae6d452 → 13ef008). The pre-rewrite commits are not recoverable locally.
- **Commits on main**: 1402 (after rewrite)
- **docs/PHASE_3_ACTUAL_STATE.md**: Not in working tree. Was deleted in commit `abb4454` ("Phase 8: Remove all docs migrated to AnythingLLM"). The file containing the redacted token no longer exists. The filter-branch rewrote the token value to `REDACTED_VAULT_ROOT_TOKEN` in all historical commits that contained the file.
- **Token removed**: `REDACTED_VAULT_ROOT_TOKEN` — GitHub push protection confirmed the rewrite succeeded (push went through).
- **No dangling objects**: gc --prune=now was run. Old commit objects are gone.

---

## 5. CONTAINERS vs SERVICE REGISTRY

- **Running containers**: 55
- **Registry entries**: 61
- **Registry entries with `container: null`** (Obot shims): 17 — expected, these are dynamic

### Containers running but NOT in registry (17):
All are Obot-spawned dynamic shims matching `ms1xxxxx` pattern. The registry covers these under `obot-shim-generic-a/b/c` and named shims (`obot-shim-strava`, etc.) with `container: null`. The CMDB validator already handles this with WARN_UNDOCUMENTED (non-fatal).

Current dynamic shims running:
`ms14fpds`, `ms14fpds-shim`, `ms18jq7z`, `ms18jq7z-shim`, `ms1b4cj8`, `ms1b4cj8-shim`, `ms1gzwnt`, `ms1gzwnt-shim`, `ms1hmn6g`, `ms1hmn6g-shim`, `ms1jqn26`, `ms1jqn26-shim`, `ms1kb8jv`, `ms1kb8jv-shim`, `ms1kf6h4`, `ms1ljkbg`, `ms1nfxvf`

Count: 17 dynamic + 1 static Obot shim (`sms1obot-mcp-server`, `sms1obot-mcp-server-shim`) = 19 undocumented containers

### Registry entries with no running container (not a failure — expected):
- `homeassistant-physical` — physical device, not a container
- `opnsense` — physical device
- `plex` — runs on QNAP, not visible to local `docker ps`
- `mcp-docker-remote` — host process (launchd), not a container
- `ollama` — registered but not currently running as a container (runs as host process or was stopped)

---

## 6. STRAVA FORENSIC SUMMARY

**Conclusion: A Strava refresh_token has never existed on this system.**

Evidence trail:
- `phase-10-validation-report.md` (written at Phase 10 completion): `STRAVA_REFRESH_TOKEN: ❌ Not configured — token will expire`
- Same report notes the `strava-mcp` npm package is "an incomplete placeholder that returns `under_construction`"
- `docker/.env`: Contains `STRAVA_CLIENT_ID`, `STRAVA_CLIENT_SECRET`, `STRAVA_ACCESS_TOKEN` — no `STRAVA_REFRESH_TOKEN` field exists at all
- `secret/strava/oauth` in Vault: `refresh_token = n/a` (literal string, set by this session)
- `config/obot/tools.yaml`: References `${STRAVA_REFRESH_TOKEN}` as an env var — never populated
- `bin/register_obot_tools.py`: `STRAVA_REFRESH_TOKEN = os.environ.get("STRAVA_REFRESH_TOKEN", "")` — always empty string
- The access token in `docker/.env` (`9258125c4844db3d87b2861bae7ea0c7a8464983`) was verified invalid via Strava API call this session

**The Strava OAuth authorization grant (user → browser → code → token exchange) was never completed.**

---

## 7. CRON JOB FAILURE PREDICTION

| Job | Time | Will Run | Will Succeed | Failure Mode |
|-----|------|----------|-------------|-------------|
| backup.sh | 02:00 daily | ✅ | ✅ | — |
| refresh-strava-token.sh | every 30 min | ✅ | ❌ | refresh_token="n/a"; curl to Strava returns 400; script exits 1; logged to /var/log/strava-refresh.log |
| sync-strava-to-calendar.py | 06:00 daily | ✅ | ❌ | access_token="n/a"; Vault get returns "n/a"; Strava API returns 401; script prints error and exits |

---

## 8. RECOMMENDATIONS (NOT EXECUTED — AUDIT ONLY)

1. **Strava**: Complete OAuth authorization flow to obtain initial refresh_token. One browser action required — no workaround exists.

2. **Secrets in .env not in Vault**: Migrate `PLEX_TOKEN`, `QNAP_PASS`, `SEEDBOX_PASSWORD`, `GITHUB_TOKEN`, `PLANE_API_TOKEN`, `PLANE_ADMIN_PASSWORD`, `OBOT_ADMIN_PASSWORD`, `HA_TOKEN`, `HOMEPAGE_VAR_HASS_TOKEN`, `HOMEPAGE_VAR_OWM_KEY` to Vault.

3. **Compose files reading .env instead of Vault**: Nextcloud, Vaultwarden, Zabbix compose files read credentials from `.env` files at runtime. The Vault copies are out-of-band documentation only — rotation in Vault does not affect running containers. Either wire Vault Agent sidecar injection or accept this as a known gap.

4. **secret/seedbox**: Empty path. Either populate it or delete it.

5. **secret/arr/* urls**: Use `mac-mini.internal` which requires Unbound to be running. If Unbound stops, Arr stack Vault lookups break. Consider using `192.168.10.145` or `localhost` instead.

6. **Obot shim count**: 19 undocumented containers (17 dynamic + 2 static shims). The registry has 10 named shim slots (`obot-shim-*`) plus 3 generic. Currently 19 are running. Either expand the registry generic slots or document that dynamic shim count is uncapped.

7. **docker/.env.bak**: Contains same credentials as `docker/.env`. Confirm it is gitignored (it is) and that it does not contain any credentials not in the main `.env`.
