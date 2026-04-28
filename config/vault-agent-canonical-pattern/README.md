# Vault Agent canonical pattern (H1 §6, vaultwarden as exemplar)

**Status**: pattern designed and templated. **NOT YET APPLIED** to any service. Use this template as the starting point when rolling out §6 sidecars.

## Files

- `agent.hcl` — Vault Agent config: AppRole auth, render template once, exit (`exit_after_auth = true`).
- `credentials.env.tmpl` — vaultwarden-specific template rendering `ADMIN_TOKEN={{ .Data.data.admin_token }}` from `secret/vaultwarden/admin`.

## Per-service application steps

1. Copy `agent.hcl` and `credentials.env.tmpl` into `<service>-stack-dir/vault-agent/`.
2. Edit `credentials.env.tmpl` to render the credential field names that service expects.
3. Add a sidecar service block to that service's `docker-compose.yml`:

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
      - vault-secrets-<svc>:/vault/secrets
      - ./vault-agent/agent.hcl:/vault/config/agent.hcl:ro
      - ./vault-agent/credentials.env.tmpl:/vault/agent-config/credentials.env.tmpl:ro
    command: agent -config=/vault/config/agent.hcl
    networks:
      - control-center-net
```

4. Modify the main service entry to add:
   - `depends_on: { vault-agent-<svc>: { condition: service_completed_successfully } }`
   - `volumes: - vault-secrets-<svc>:/vault/secrets:ro`
   - `entrypoint: ["sh", "-c", ". /vault/secrets/credentials.env && exec <original-entrypoint>"]`
   - Remove credential entries from `environment:` block.

5. Add the named volume:

```yaml
volumes:
  vault-secrets-<svc>:
    driver: local
    driver_opts:
      type: tmpfs
      device: tmpfs
```

6. `docker compose up -d` — vault-agent runs once, renders `/vault/secrets/credentials.env`, exits; main service starts and sources the rendered env file.

7. Verify per amendment 2 (category-specific):
   - Web: API hit using delivered key returns non-401
   - Worker: `docker logs <svc>` shows zero `error|fail|panic` in 30s
   - DB: `pg_isready`
   - MCP: `/healthz` + env check
   - Vault: token lookup

8. Delete the now-unused `.env` file once main service is healthy.

## Why exit_after_auth + tmpfs (not long-running agent)

Static secrets (admin tokens, DB passwords) don't rotate often. `exit_after_auth=true` renders once per compose-up cycle, then the sidecar exits cleanly — no zombie processes. Rotation is a `docker compose down && up` cycle. tmpfs ensures rendered credentials live only in volatile memory.

For dynamic secrets (Vault dynamic Postgres creds, PKI certs), use `exit_after_auth = false` with a `template { command = "..." }` post-render hook to signal the application.
