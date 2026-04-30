# Phase 15 — seal-vault Blocker (D#32)

**Date:** 2026-04-30
**Status:** OPEN — requires operator decision
**Blocking:** Block F (network-discovery live run), Block G (Plane curation)

## Root Cause

seal-vault (Transit auto-unseal provider for vault-server) entered a broken state after a Colima VZ restart that was triggered during a test container run earlier in the session. After the restart, the Vault 2.0.0 binary runs inside the container but produces zero log output and does not bind port 8201. The vault process IS running (confirmed via `ps aux`), but the listener never starts.

Confirmed behaviors:
- `vault version` works (binary is functional)
- `vault server -config=...` starts but hangs silently — no stdout, no port binding
- The issue appeared after Colima restart; was NOT present in prior sessions
- Removing the stale `.lock` file from the `seal-vault-data` volume did not resolve it
- Bypassing `dumb-init` (the image's shebang handler) did not resolve it
- Adding `SKIP_CHOWN=true` did not resolve it
- `cap_drop: [ALL]` was present before the failure with no issues
- The Colima VZ kernel version after restart may have a seccomp/capability interaction with the vault 2.0.0 Go runtime that blocks listener initialization

## Current seal-vault Config State

`/Users/admin/control-center-stack/stacks/seal-vault/docker-compose.yml` has been updated with:
- `SKIP_CHOWN: "true"` — safe, keeps
- `entrypoint: ["/bin/sh", "/usr/local/bin/docker-entrypoint.sh"]` — bypasses dumb-init
- Original `command: ["server"]` — unchanged
- `cap_drop: [ALL]` — restored (was temporarily removed during debug)

`config/vault-config.hcl` — restored to original (including `enable_unauthenticated_access`).

## Recovery Options

### Path A — Nuclear reset (15 min, operator required)
Destroys seal-vault data volume and re-initializes from scratch:

```bash
cd /Users/admin/control-center-stack/stacks/seal-vault
docker compose down
docker volume rm seal-vault_seal-vault-data seal-vault_seal-vault-logs
docker compose up -d
sleep 10
# Initialize seal-vault (1-of-1 Shamir)
docker run --rm --network control-center-net curlimages/curl:latest \
  -s -X PUT http://seal-vault:8201/v1/sys/init \
  -H "Content-Type: application/json" \
  -d '{"secret_shares":1,"secret_threshold":1}'
# Save the new unseal key and root token from the response
# Update vault-server's transit seal config with the new root token
# Re-create the autounseal transit key and policy
```

Note: vault-server will need to be re-wrapped with the new Transit credentials.

### Path B — Downgrade seal-vault image
Try `hashicorp/vault:1.18` which uses the same dumb-init entrypoint but an older Go runtime:

```bash
# Edit docker-compose.yml: image: hashicorp/vault:1.18
# docker compose down && docker compose up -d
# Attempt unseal: key = 0JMOGBgUtGguB9H5DjIQ/lTIcbqmljasP85jyAKUnV0=
```

### Path C — Colima full restart with clean state
A clean `colima delete && colima start --fresh` might reset the kernel state that's blocking the vault runtime. Risk: all Docker volumes persist (they're in `/var/lib/docker/volumes` inside Colima VM), but all running containers stop and restart.

## Downstream Impact

All Vault-dependent services are degraded:
- `vault-server`: unhealthy (sealed, can't auto-unseal without seal-vault)
- `plane-api`: restart loop — missing `/vault/secrets/credentials.env`
- `mcpo-proxy`: unhealthy — stale credentials.env from last vault-agent run (still functional for now)
- All other vault-agent-* sidecars: exited, credentials stale

Services NOT affected (no vault dependency):
- Caddy, Sonarr, Radarr, Prowlarr, Plex, Nextcloud, Grafana, Zabbix, NetBox, Plane-web/db/redis

## Phase 15 Items Remaining

| Block | Item | Status |
|-------|------|--------|
| F | 4.J network-discovery dry-run | Blocked (needs NetBox token from Vault) |
| F | launchd plist for nightly discovery | Pending dry-run success |
| G | Plane backlog curation | Blocked (plane-api in restart loop) |
| - | Regression probe | Blocked (Vault services unhealthy) |
