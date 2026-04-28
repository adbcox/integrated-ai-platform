# Phase 13 Block H1 — CHECKPOINT (not completion)

**Date**: 2026-04-29
**Status**: §0–§5 complete and verified. §6 partial (canonical pattern only, 0 of 12 services rewired). §7–§14 pending.

This document captures the exact system state at H1 checkpoint so a fresh execution session can pick up at §6 phase A without ambiguity.

---

## What's complete (committed, runnable)

### §0 — Pre-flight + rollback prep
- Pre-H1 state captured to `docs/phase-13/h1-rollback-state/` (gitignored — contains deleted credential backups).
- `docs/phase-13/h1-rollback-state/rollback.sh` is syntactically valid and contains undo blocks for §0 base + §1 + §2 + §3 + §4 + §5.
- Vault token healthy: ttl ≈30 days, orphan, root.

### §1 — .env file resolution
**Deleted (4 files, all credential-bearing)**:
1. `/Users/admin/control-center-stack/stacks/vault/.env` (revoked root token; verified 403 on lookup)
2. `/Users/admin/repos/integrated-ai-platform/backups/phase16-20260427-172029/` (entire 49-field backup, all migrated)
3. `/Users/admin/arr-backups/20260426/rclone/rclone-health.env` (3 stale arr keys, all in Vault)
4. `/Users/admin/control-plane/.env` (separate-repo .env, PLANE_API_TOKEN already in Vault)

**Migrated to Vault during §1** (9 new fields):
- `secret/plane/admin:email`
- `secret/qnap/admin:username`
- `secret/seedbox/account:username`
- `secret/anthropic/api:api_key`
- `secret/openai/api:api_key`
- `secret/litellm/master:master_key`
- `secret/open-webui/app:secret_key`
- `secret/zabbix/db:{username, database, password}`
- `secret/openhands/llm:{api_key, base_url, model}`

**5 active .env files still in service queue (pending §6 rewire)**:
1. `/Users/admin/repos/integrated-ai-platform/docker/.env` — 49 fields, consumed by 50+ services via Compose `env_file`
2. `/Users/admin/repos/integrated-ai-platform/docker/nextcloud/.env` — `NEXTCLOUD_ADMIN_PASSWORD`, `NEXTCLOUD_DB_PASSWORD`
3. `/Users/admin/repos/integrated-ai-platform/docker/vaultwarden/.env` — `ADMIN_TOKEN`
4. `/Users/admin/repos/integrated-ai-platform/docker/zabbix/.env` (+ `.env.zabbix-admin`) — `POSTGRES_PASSWORD`, `ZABBIX_ADMIN_PASSWORD`, others
5. `/Users/admin/repos/integrated-ai-platform/config/oss_wave/openhands.env` — `LLM_API_KEY` etc.

Plus 2 outside-the-repo files also queued:
6. `/Users/admin/control-center-stack/stacks/gateways/.env` — `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `LITELLM_MASTER_KEY`, `PLANE_API_TOKEN`
7. `/Users/admin/control-center-stack/stacks/ai-control/.env` — `LITELLM_MASTER_KEY`, `WEBUI_SECRET_KEY`

All 7 files are listed in `docs/phase-13/h1-rollback-state/h1-rewire-queue.txt`. All credentials they contain are already in Vault under canonical paths. Files remain in place because compose stacks still consume them at runtime.

### §2 — Backup script repair
- AppRole `backup` created with policy granting only `secret/restic/backup` + `secret/minio/backup`.
- `~/.vault-approle/backup/{role-id, secret-id}` mode 600.
- `secret/restic/backup` enriched with `repository = s3:http://192.168.10.201:9000/backups`.
- `scripts/backup.sh` rewritten: AppRole login → 1h-TTL token → reads creds via API → revokes own token on EXIT.
- New Restic snapshot **`9d7fdfff`** verified end-to-end against MinIO on QNAP.

### §3 — Vault audit logging
- File audit device enabled at `/vault/logs/audit.log` inside vault-server container.
- `secret/audit/retention` documents `local_days=30, rotation_size_mb=100, archive_path=/Users/admin/mnt/qnap-downloads/audit-archive/vault, rotation_path=/Users/admin/control-center-stack/stacks/vault/logs`.
- §3.4 (rotation launchd) and §3.5 (archive launchd) deferred to §4 per user-approved Option B.

### §4 — Transit auto-unseal
- **seal-vault container** running on `:8201` (Shamir 1-of-1, named volumes `seal-vault-data` + `seal-vault-logs`, network `control-center-net`).
- `~/seal-vault-init-keys-MOVE-OFFLINE.txt` (mode 600) contains seal-vault unseal key + root token. **User must move offline and delete from filesystem.**
- Transit engine + `transit/keys/autounseal` + `autounseal` policy + periodic 24h token created on seal-vault.
- Main vault config (`/Users/admin/control-center-stack/stacks/vault/vault-config.hcl`, mode 600) has `seal "transit"` stanza with inline token (control-center-stack is not git-tracked).
- Vault data migrated from Shamir → Transit (3 keys provided with `-migrate`); confirmed `type=transit, sealed=false, migration=false`.
- Restart test: `docker restart vault-server` → comes up unsealed automatically.
- **Architectural pivot from plan**: bind-mount `/vault/logs` to host failed (Colima/macOS chown issue). Switched to named volume + `docker exec` pattern in launchd jobs.

### §4.7 — Deferred §3 launchd items
- `/Users/admin/.platform-scripts/vault-audit-rotate.sh` (mode 755, tested) — rotates audit.log inside vault-server when >100MB; sends SIGHUP.
- `/Users/admin/.platform-scripts/vault-audit-archive.sh` (mode 755, tested) — gzip-streams rotated logs from container to QNAP `audit-archive/vault/`.
- `/Users/admin/Library/LaunchAgents/com.adbcox.vault-audit-rotate.plist` and `com.adbcox.vault-audit-archive.plist` in place (StartCalendarInterval 03:00 / 03:30).
- **Active scheduling: user crontab** (immediately fires at 03:00 / 03:30):
  ```
  0 3 * * * /Users/admin/.platform-scripts/vault-audit-rotate.sh ...
  30 3 * * * /Users/admin/.platform-scripts/vault-audit-archive.sh ...
  ```
- launchd plists not loaded in this session (Claude Code shell lacks audit-session privileges; pre-existing platform plists like `com.iap.mcp.docker` are in same state). User can manually run in Terminal:
  ```bash
  launchctl bootstrap user/$(id -u) ~/Library/LaunchAgents/com.adbcox.vault-audit-rotate.plist
  launchctl bootstrap user/$(id -u) ~/Library/LaunchAgents/com.adbcox.vault-audit-archive.plist
  ```

### §5 — Per-service AppRoles (status of all 22)

All 22 AppRoles created with scoped policies. `~/.vault-approle/<svc>/{role-id, secret-id}` mode 600. All policies committed to `config/vault-policies/`. Isolation verified for sonarr (✓ in-policy READ, ✓ out-of-policy DENIED) and litellm-gateway (✓ all 4 in-policy paths read).

| # | Service | AppRole | Policy file | Vault paths granted (read-only) | Used by §6? |
|---|---|---|---|---|---|
| 1 | sonarr | ✓ | `config/vault-policies/sonarr-policy.hcl` | `secret/arr/sonarr` | NO (internal API key) |
| 2 | radarr | ✓ | `config/vault-policies/radarr-policy.hcl` | `secret/arr/radarr` | NO (internal API key) |
| 3 | prowlarr | ✓ | `config/vault-policies/prowlarr-policy.hcl` | `secret/arr/prowlarr` | NO (internal API key) |
| 4 | plex-mcp | ✓ | `config/vault-policies/plex-mcp-policy.hcl` | `secret/plex/api` | NO (internal config) |
| 5 | nextcloud | ✓ | `config/vault-policies/nextcloud-policy.hcl` | `secret/nextcloud/{admin,db}` | YES |
| 6 | vaultwarden | ✓ | `config/vault-policies/vaultwarden-policy.hcl` | `secret/vaultwarden/admin` | YES |
| 7 | zabbix-server | ✓ | `config/vault-policies/zabbix-server-policy.hcl` | `secret/zabbix/{admin,db}` | YES |
| 8 | zabbix-web | ✓ | `config/vault-policies/zabbix-web-policy.hcl` | `secret/zabbix/{admin,db}` | YES |
| 9 | zabbix-postgres | ✓ | `config/vault-policies/zabbix-postgres-policy.hcl` | `secret/zabbix/db` | YES (DB init) |
| 10 | openhands-app | ✓ | `config/vault-policies/openhands-app-policy.hcl` | `secret/openhands/llm` | YES |
| 11 | litellm-gateway | ✓ | `config/vault-policies/litellm-gateway-policy.hcl` | `secret/{anthropic,openai,litellm/master,plane/api}` | YES |
| 12 | open-webui | ✓ | `config/vault-policies/open-webui-policy.hcl` | `secret/open-webui/app, secret/litellm/master` | YES |
| 13 | obot | ✓ | `config/vault-policies/obot-policy.hcl` | `secret/obot/admin, secret/github/api` | YES |
| 14 | homeassistant | ✓ | `config/vault-policies/homeassistant-policy.hcl` | `secret/homeassistant/api` | (defer) |
| 15 | plane-api | ✓ | `config/vault-policies/plane-api-policy.hcl` | `secret/plane/{admin,api,app,minio}` | YES |
| 16 | plane-web | ✓ | `config/vault-policies/plane-web-policy.hcl` | `secret/plane/{admin,api}` | YES |
| 17 | plane-worker | ✓ | `config/vault-policies/plane-worker-policy.hcl` | `secret/plane/{api,app}` | YES |
| 18 | plane-beat | ✓ | `config/vault-policies/plane-beat-policy.hcl` | `secret/plane/{api,app}` | YES |
| 19 | grafana-obs | ✓ | `config/vault-policies/grafana-obs-policy.hcl` | `secret/grafana/api` | (defer) |
| 20 | headscale | ✓ | `config/vault-policies/headscale-policy.hcl` | `secret/headscale/admin` | (defer) |
| 21 | strava-sync | ✓ | `config/vault-policies/strava-sync-policy.hcl` | `secret/strava/oauth` | (defer; host-script not container) |
| 22 | homepage | ✓ | `config/vault-policies/homepage-policy.hcl` | `secret/{homeassistant,plex,arr/*,openweathermap}/api` | YES |

Plus the previously-created `backup` AppRole (§2).

---

## What's partial (§6) — DO NOT USE WITHOUT COMPLETING

### §6 canonical pattern (built but not deployed)

Pattern files at `config/vault-agent-canonical-pattern/` (committed):
- `agent.hcl` — Vault Agent config: AppRole auth, render-once-and-exit (`exit_after_auth = true`).
- `credentials.env.tmpl` — vaultwarden-specific template (rendering `ADMIN_TOKEN` from `secret/vaultwarden/admin`).
- `README.md` — full per-service application steps.

**Vaultwarden was NOT rewired**. The pattern files exist as documentation. Vaultwarden continues running with its existing `.env` file consumption. No partial mutation has been applied to any compose stack.

### §6 phase A target (12 services for next-session execution)

In strict dependency order:

**Phase A (independent)**: vaultwarden, openhands-app, litellm-gateway, open-webui (4 services)
**Phase B (DBs)**: nextcloud-db (postgres init), zabbix-postgres (init), docker-plane-db (init) (3 services)
**Phase C (DB clients)**: nextcloud, zabbix-server, zabbix-web, plane-{api,web,worker,beat}, obot (8 services)
**Phase D (cross-cutting)**: homepage (reads many other services' API keys) (1 service)
**Phase E**: caddy — no rewire needed (no credentials)
**Phase F**: vault — already auto-unsealed via Transit (no rewire needed)

10 services that were in §5 inventory but **don't need §6 sidecars** (have internal API keys, no startup credential consumption): sonarr, radarr, prowlarr, plex-mcp, sportarr, mcp-* servers, vmagent, vm, node-exporter, uptime-kuma. Their AppRoles + policies are still useful — they let _consumers_ (homepage, scripts) read those services' API keys from Vault.

### Partial mutations

**None requiring revert or completion.** The only mutations made were:
- File deletions (committed via rollback-state preservation; rollback.sh restores)
- Vault state changes (audit enabled, AppRoles created, transit migration) — all desired end state
- New containers running (seal-vault) — desired
- Compose file edits (vault stack only: vault-config.hcl + docker-compose.yml) — applied and operational
- Scripts created (backup.sh rewritten, vault-audit-*.sh new) — applied and tested

No half-rewired services. No half-applied compose mutations. The system is in a stable runnable state.

---

## What's pending (§6 remainder + §7–§14)

| § | Title | Estimated effort |
|---|---|---|
| 6 (rest) | Rewire 11 remaining services per phases A-F | 3–4 h |
| 7 | Container hardening (22 root-running containers) | 3–4 h |
| 8 | Pre-commit + detect-secrets baseline | 30 min |
| 9 | Untracked files cleanup | 30 min |
| 10 | Service dependency graph + per-host vault.hcl | 1 h |
| 11 | Runbooks (7 files) | 2 h |
| 12 | Docker events capture (launchd/cron) | 15 min |
| 13 | CLAUDE.md "Platform Rules — Non-Negotiable" | 15 min |
| 14 | Final audit + fresh-session validation + commit | 30 min |

**Total remaining**: 11–13 hours focused work.

---

## Rollback script state

`docs/phase-13/h1-rollback-state/rollback.sh` (gitignored):
- §0 base: stops seal-vault + vault-agent-* containers; restores vault-config.hcl, service-registry.yaml, .gitignore; uninstalls pre-commit; restarts vault-server.
- §1 undo: restores 4 deleted .env files (vault stack, phase16, rclone-health, control-plane).
- §2 undo: restores pre-H1 backup script (the broken one with revoked token).
- §3 undo: disables file audit device.
- §4 undo: restores vault-config.hcl + docker-compose.yml from `.pre-h1-section4` backups; tears down seal-vault; recreates vault-server (will be sealed; manual Shamir unseal required).
- §5 undo: deletes 22 AppRoles + policies; removes `~/.vault-approle/<svc>/` directories.
- (FINALIZE block last)

Syntax validated `bash -n` after each section append. Does not execute idempotently across multiple runs (designed for one-shot revert).

---

## Resume protocol for next session

1. Read this file plus `PHASE_13_BLOCK_H1_RESULTS_2026-04-29.md` (the full per-section log).
2. Verify checkpoint state still holds: `docker ps`, `docker exec vault-server vault status`, audit log size growth, AppRole listing.
3. Begin §6 Phase A with vaultwarden (simplest case: 1 secret) using `config/vault-agent-canonical-pattern/` as the template.
4. Apply category-specific verification per amendment 2 (web/worker/db/mcp/vault).
5. Strict 6-phase gate per amendment 3.
6. Continue through §7–§14.
7. §14.6 fresh-session validation as new shell, no exported `VAULT_TOKEN`.

H1 is **NOT YET COMPLETE**. This is a checkpoint only.
