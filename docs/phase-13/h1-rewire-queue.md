# H1 §6 Rewire Queue — Authoritative Roster

**Generated**: 2026-04-28 (Phase 0 closure)
**Source of truth**: This file. Replaces all prior service-count statements in CHECKPOINT and RESULTS docs.

---

## Tracked deferred user actions

1. **seal-vault keys at temporary holding location**: `~/Documents/pending-offline-storage/seal-vault-keys.txt` (697 bytes, mode 600). User commits to moving to USB + printed copy in fire safe when higher-quality USB drive arrives (afternoon of 2026-04-28). **§14 fresh-session validation is gated on this completion.**

---

## Database password posture (Phase 0 spot-check)

| Path | Length | Strength | Action |
|---|---|---|---|
| `secret/nextcloud/db` | 44 (base64-shaped) | STRONG | none |
| `secret/zabbix/db` | 31 | STRONG | none |
| `secret/plane/db` | 5 (`p***e`, upstream default) | WEAK | **Rotate during Phase C plane rewire (Option γ)** |

Plane-db rotation procedure (executed during Phase C, before plane-api/web/worker/beat sidecar rewire):
1. Generate: `openssl rand -base64 32 | tr -d '/+=' | cut -c1-32`
2. `vault kv put secret/plane/db password=<new>`
3. `docker exec docker-plane-db-1 psql -U <user> -c "ALTER USER <user> WITH PASSWORD '<new>';"`
4. Recreate plane-{api,web,worker,beat} with sidecars reading new value
5. Then rewire plane-db with sidecar (Phase B step deferred to land after rotation)
6. Document old/new lengths + sha256 prefixes in rewire log for audit trail

---

## Service roster (16 active rewires)

Phases reflect dependency ordering and §6/§7 coordination doctrine (each service `docker compose up --force-recreate <svc>` exactly once with both sidecar AND §7 hardening applied).

| # | Service | AppRole | Vault paths | Cred fields | Phase | Compose location |
|---|---|---|---|---|---|---|
| 1 | vaultwarden | vaultwarden | `secret/vaultwarden/admin` | 1 (ADMIN_TOKEN) | A | `~/repos/integrated-ai-platform/docker/vaultwarden/` |
| 2 | openhands-app | openhands-app | `secret/openhands/llm` | 3 (api_key, base_url, model) | A | (TBD — bring under compose at `~/repos/integrated-ai-platform/docker/openhands/`) |
| 3 | litellm-gateway | litellm-gateway | 4 paths (anthropic, openai, litellm/master, plane/api*) | 3 confirmed + 1 to verify | A | `~/control-center-stack/stacks/gateways/` (out-of-repo) |
| 4 | open-webui | open-webui | `secret/open-webui/app, secret/litellm/master` | 2 (WEBUI_SECRET_KEY, OPENAI_API_KEY=litellm-master) | A | `~/control-center-stack/stacks/ai-control/` (out-of-repo) |
| 5 | nextcloud-db | nextcloud-db (NEW) | `secret/nextcloud/db` | 1 (POSTGRES_PASSWORD) | B | `~/repos/integrated-ai-platform/docker/nextcloud/` |
| 6 | zabbix-postgres | zabbix-postgres | `secret/zabbix/db` | 1 (POSTGRES_PASSWORD) | B | `~/repos/integrated-ai-platform/docker/zabbix/` |
| 7 | docker-plane-db | plane-db (NEW) | `secret/plane/db` | 1 (POSTGRES_PASSWORD, rotated in Phase C) | B (after rotation) | `~/repos/integrated-ai-platform/docker/` (`docker-compose-plane.yml`) |
| 8 | nextcloud | nextcloud | `secret/nextcloud/{admin,db}` | 2 (NEXTCLOUD_ADMIN_PASSWORD, POSTGRES_PASSWORD) | C | `~/repos/integrated-ai-platform/docker/nextcloud/` |
| 9 | zabbix-server | zabbix-server | `secret/zabbix/{admin,db}` | 2-3 (POSTGRES_PASSWORD primary; ZABBIX_ADMIN at first init only) | C | `~/repos/integrated-ai-platform/docker/zabbix/` |
| 10 | zabbix-web | zabbix-web | `secret/zabbix/{admin,db}` | 1-2 (POSTGRES_PASSWORD primary) | C | `~/repos/integrated-ai-platform/docker/zabbix/` |
| 11 | docker-plane-api | plane-api | `secret/plane/{admin,api,app,minio}` | 4+ (SECRET_KEY, AWS_*, REDIS, etc.) | C | `~/repos/integrated-ai-platform/docker/` |
| 12 | docker-plane-web | plane-web | `secret/plane/{admin,api}` | TBD (verified during rewire) | C | `~/repos/integrated-ai-platform/docker/` |
| 13 | docker-plane-worker | plane-worker | `secret/plane/{api,app}` | TBD | C | `~/repos/integrated-ai-platform/docker/` |
| 14 | docker-plane-beat | plane-beat | `secret/plane/{api,app}` | TBD | C | `~/repos/integrated-ai-platform/docker/` |
| 15 | docker-plane-minio | plane-minio (NEW) | `secret/plane/minio` | 2 (username, password) | C (with plane stack) | `~/repos/integrated-ai-platform/docker/` |
| 16 | obot | obot | `secret/obot/admin, secret/github/api` | 2 (OBOT_ADMIN_PASSWORD, GITHUB_TOKEN) | C | `~/repos/integrated-ai-platform/docker/` (`obot-stack.yml`) |

**Dropped from §6**: homepage (Gap 9 — not currently deployed; will be rewired at deploy-time using canonical pattern).

**No-sidecar services in rewire queue**: caddy (Phase E, §7 hardening only), vault-server (Phase F, §7 only).

## Naming convention

Sidecar container names follow `vault-agent-<approle-name>`. AppRoles match the table above. Application container names unchanged (e.g., `docker-plane-api-1` retains its name; sidecar is `vault-agent-plane-api`).

## Compose-location split

**In-repo** (git-tracked): vaultwarden, nextcloud, nextcloud-db, zabbix-{postgres,server,web}, plane (5 containers), obot, openhands-app (after compose conversion).
**Out-of-repo** (`~/control-center-stack/`, not git-tracked): litellm-gateway, open-webui.

Out-of-repo edits do not flow through standard git review. Pre/post snapshots written to `docs/phase-13/h1-rollback-state/<svc>-pre-rewire/` for both. To be documented in §13 CLAUDE.md platform rules.

## AppRole inventory (post Phase 0)

26 AppRoles total: 22 from §5 + `backup` (§2) + 3 new from Phase 0 (`nextcloud-db`, `plane-db`, `plane-minio`).

```
backup, grafana-obs, headscale, homeassistant, homepage, litellm-gateway,
nextcloud, nextcloud-db, obot, open-webui, openhands-app,
plane-api, plane-beat, plane-db, plane-minio, plane-web, plane-worker,
plex-mcp, prowlarr, radarr, sonarr, strava-sync, vaultwarden,
zabbix-postgres, zabbix-server, zabbix-web
```

Isolation verified for 3 new AppRoles: each can read its own path, denied on adjacent service paths.

## Render scope per service

**Doctrine**: sidecar templates render only credential fields. Non-cred config (POSTGRES_USER, POSTGRES_DB, etc.) stays in compose `environment:` block. This matches §5 policy granularity (paths granted only contain cred fields).

## Phase A sequencing (intra-phase gating)

A.1 vaultwarden — canonical pattern proof against simplest, already-compose-managed service.
A.2 GATE — pattern proven, README accurate, no flaws.
A.3 openhands-app — compose conversion + sidecar in one recreation.
A.4 GATE — openhands-app stable.
A.5 litellm-gateway.
A.6 GATE.
A.7 open-webui.
A.8 GATE — Phase A close.

Each intra-phase gate is independently passed before the next sub-service starts. No bundling of canonical-pattern proof with compose-conversion-plus-sidecar work on a never-compose-managed service.

## Per-service verification step — litellm-gateway (A.5)

**Phase A verification**: confirm whether `secret/plane/api` token is actually consumed by litellm. If not consumed, remove the path from `litellm-gateway-policy.hcl`. Don't carry over policy paths that aren't actually used.

litellm-gateway AppRole grants `secret/data/plane/api`. Container env shows LITELLM_MASTER_KEY, ANTHROPIC_API_KEY, OPENAI_API_KEY, but PLANE_API_TOKEN was NOT visible in the running container env. During Phase A litellm rewire (step A.5), inspect the compose file for `PLANE_API_TOKEN`. If absent:
- Remove `path "secret/data/plane/api" { capabilities = ["read"] }` from `config/vault-policies/litellm-gateway-policy.hcl`
- Reload: `vault policy write litellm-gateway config/vault-policies/litellm-gateway-policy.hcl`
