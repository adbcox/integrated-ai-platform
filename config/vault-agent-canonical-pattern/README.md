# Vault Agent canonical pattern (H1 §6, vaultwarden as exemplar)

**Status**: pattern designed and templated. **NOT YET APPLIED** to any service. Use this template as the starting point when rolling out §6 sidecars.

## Files

- `agent.hcl` — Vault Agent config: AppRole auth, render template once, exit (`exit_after_auth = true`).
- `credentials.env.tmpl` — vaultwarden-specific template rendering `ADMIN_TOKEN={{ .Data.data.admin_token }}` from `secret/vaultwarden/admin`.

## Storage mechanism: host bind-mount (macOS / Colima)

After Phase 0 empirical testing on 2026-04-28, the canonical mechanism for storing rendered credentials is a **host bind-mount** from the Mac filesystem into both the sidecar (write) and the main service (read-only). Real tmpfs sharing across containers is not viable on macOS/Colima — see KNOWN-LIMITATION below.

**Per-service host directory**: `/Users/admin/.vault-agent-secrets/<svc>/`
- Created mode 0700 by the rewire procedure (admin-only)
- Sidecar (vault uid 100) writes `credentials.env` mode 0444 via the agent template
- Main service mounts the directory read-only at `/vault/secrets`

### KNOWN-LIMITATION (macOS/Colima)

> On macOS/Colima, rendered credentials persist briefly to host disk at `/Users/admin/.vault-agent-secrets/<svc>/credentials.env`. Mode 0500, admin-only readable. Risk: if the host disk is imaged or the file is accessed before being overwritten by next render, credentials are exposed. Mitigations: full-disk encryption (FileVault) on Mac Mini, mode 0500, regular re-render cycles. On Linux deployments (Threadripper), use real tmpfs mount instead.

### What was rejected and why

- **Named volume with `driver_opts: type=tmpfs`** — DOES create tmpfs inside containers, but tmpfs is per-mount-namespace. When the sidecar exits and no other container holds the volume, the tmpfs is freed. Files do NOT persist to the main service. **Empirically validated: failed**.
- **Compose `tmpfs:` block (per-container tmpfs mount)** — same limitation: each container gets its own tmpfs; cannot be shared sidecar→main.
- **Host bind-mount of `/Users/admin/.vault-agent-secrets/<svc>/`** — works. Vault Agent (uid 100 in container) writes successfully via Colima's UID mapping; main service reads as its own user. **Selected as canonical.**
- **Regular Docker named volume (no tmpfs opt) — Option 2d, viable per-service fallback** — also works (persists to Colima VM ext4 at `/var/lib/docker/volumes/<vol>/_data/`). Equivalent security profile (on disk; protected by FileVault + admin-only `colima ssh` + root-owned within VM). **Use only as a per-service fallback** if host bind-mount Option 2 hits permission/UID conflicts on a specific service. Do not switch to Option 2d preemptively.

## Per-service application steps

1. Copy `agent.hcl` and `credentials.env.tmpl` into `<service>-stack-dir/vault-agent/`.
2. Edit `credentials.env.tmpl` to render the credential field names that service expects.
3. Create the host secrets directory:
   ```bash
   mkdir -p /Users/admin/.vault-agent-secrets/<svc>
   chmod 0700 /Users/admin/.vault-agent-secrets/<svc>
   ```
4. Add a sidecar service block to that service's `docker-compose.yml`:

```yaml
  vault-agent-<svc>:
    image: hashicorp/vault:2.0.0
    container_name: vault-agent-<svc>
    restart: "no"   # exit_after_auth=true; runs once per compose-up
    environment:
      VAULT_ADDR: "http://vault-server:8200"
      SKIP_SETCAP: "true"
    volumes:
      - /Users/admin/.vault-approle/<svc>:/vault/approle:ro
      - /Users/admin/.vault-agent-secrets/<svc>:/vault/secrets
      - ./vault-agent/agent.hcl:/vault/config/agent.hcl:ro
      - ./vault-agent/credentials.env.tmpl:/vault/agent-config/credentials.env.tmpl:ro
    command: agent -config=/vault/config/agent.hcl
    networks:
      - control-center-net
```

5. Modify the main service entry to add:
   - `depends_on: { vault-agent-<svc>: { condition: service_completed_successfully } }`
   - `volumes: - /Users/admin/.vault-agent-secrets/<svc>:/vault/secrets:ro`
   - `entrypoint: ["sh", "-c", ". /vault/secrets/credentials.env && exec <original-entrypoint>"]`
   - Remove credential entries from `environment:` block.

6. `docker compose up -d` — vault-agent runs once, renders `/vault/secrets/credentials.env` to the host bind-mount, exits; main service starts and sources the rendered env file from the same path.

7. Verify per amendment 2 (category-specific):
   - Web: API hit using delivered key returns non-401
   - Worker: `docker logs <svc>` shows zero `error|fail|panic` in 30s
   - DB: `pg_isready`
   - MCP: `/healthz` + env check
   - Vault: token lookup

8. Delete the now-unused `.env` file once main service is healthy.

## Why exit_after_auth + bind-mount (not long-running agent)

Static secrets (admin tokens, DB passwords) don't rotate often. `exit_after_auth=true` renders once per compose-up cycle, then the sidecar exits cleanly — no zombie processes. Rotation is a `docker compose down && up` cycle. The bind-mount means the rendered file persists across the sidecar's exit so the main service can read it (a behavior tmpfs would forfeit).

For dynamic secrets (Vault dynamic Postgres creds, PKI certs), use `exit_after_auth = false` with a `template { command = "..." }` post-render hook to signal the application.
