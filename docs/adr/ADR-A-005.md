# ADR-A-005 — Security model: Caddy TLS termination, Vault secrets, network isolation
**Status:** Accepted
**Date:** 2026-04-26
**Source:** Phase 7 container hardening and Vault migration

## Context

The platform runs on a private 192.168.10.0/24 LAN without internet exposure. Services handle LLM API keys, GitHub PATs, database credentials, SNMP community strings, and OPNsense API keys. A consistent security model was needed to avoid credentials in environment variables, plain-text config files, or Docker Compose files committed to git.

## Decision

Three-layer security model:

**1. Secret management — HashiCorp Vault (server mode):**
- All credentials stored in Vault KV v2 at `secret/` path tree
- 5-of-3 Shamir unseal — unseal keys stored at `~/vault-init-keys.txt` (not in repo)
- Services read secrets at startup via Vault agent or direct API call
- `disable_mlock=true` required on macOS (no IPC_LOCK capability)

**2. TLS termination — Caddy:**
- Caddy handles HTTPS for all user-facing services on the LAN
- Internal service-to-service communication uses plain HTTP on Docker networks (no inter-service TLS overhead)
- OPNsense firewall enforces that no service ports are exposed to WAN

**3. Container hardening baseline:**
- All containers: `cap_drop: [ALL]`, `security_opt: [no-new-privileges:true]`
- Read-only filesystem mounts where possible
- Docker networks segmented by function (plane-net, obot-net, monitoring-net, etc.) — containers only join networks they need
- Service registry `security` field documents actual vs expected baseline per service

## Consequences

- Vault must be unsealed after every Mac Mini reboot before services that read secrets can start; unsealing is manual (by design — protects against automated key extraction)
- `~/vault-init-keys.txt` must never be committed to git; it is gitignored via `.gitignore`
- Caddy auto-HTTPS requires DNS or mkcert for LAN domains; currently using IP-based access until LAN DNS is configured
- `cap_drop: [ALL]` breaks containers that need capabilities (e.g., ping, raw sockets) — add back only the specific capability needed rather than reverting the baseline
- Obot and mcpo-proxy intentionally have `OBOT_SERVER_ENABLE_AUTHENTICATION: false` in dev mode — this must be changed before any WAN exposure
