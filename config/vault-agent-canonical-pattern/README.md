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
   - `entrypoint: ["sh", "-c", "set -a && . /vault/secrets/credentials.env && set +a && exec <original-entrypoint>"]`
   - Remove credential entries from `environment:` block.

### Entrypoint wrapper — REQUIRED on main service, NOT on sidecar

The wrapper is **mandatory on the main service container** for the rendered credentials to actually reach the application process. It is **NOT used on the sidecar** — the sidecar's role ends at "render `/vault/secrets/credentials.env` and exit cleanly".

**Why `set -a` is required**:

POSIX `.` (source) loads variable assignments from a file into the **current shell** as shell-local variables. They are not exported as environment variables unless explicitly exported. When the shell then `exec`s the application binary, the application inherits the shell's **environment** (exported vars only), not its shell-local variables — so the application would not see `ADMIN_TOKEN` or any other rendered field.

`set -a` enables the auto-export attribute: every variable assigned (including via sourced files) becomes an exported environment variable for the duration. `set +a` disables it after sourcing.

**Why `exec` is required (not optional)**:

`exec <command>` replaces the shell process with `<command>`, so the application becomes PID 1 (or whatever PID the shell was). Without `exec`, the shell forks the application as a child:
- **Signal handling breaks**: `docker stop <container>` sends SIGTERM to PID 1 (the sh wrapper), which doesn't propagate to the child app. Docker waits the full grace period (10s default) then sends SIGKILL. With `exec`, PID 1 *is* the app, so SIGTERM reaches it directly and clean shutdown completes in ~0s.
- **Verification path differs**: `/proc/1/environ` shows the wrapper-shell's fork-time env (without rendered creds) instead of the app's runtime env. `exec` makes PID 1 environ authoritative.
- **Process tree zombies**: a sh wrapper that doesn't exec leaves an unnecessary parent process in the tree.

`exec` is **not optional** — every service rewire must use it.

### Two valid entrypoint-wrapper styles

Pick whichever matches the upstream image's existing pattern; the rule is the same — `set -a` then source then `exec`.

**Style 1 — `entrypoint:` override** (use when the image has a non-trivial `Entrypoint` you want to preserve):
```yaml
entrypoint: ["sh", "-c", "set -a && . /vault/secrets/credentials.env && set +a && exec <original-entrypoint> \"$$0\" \"$$@\""]
command: [<original cmd args>]
```
The `"$$0" "$$@"` pattern preserves the original `command:` arguments through the sh wrapper. The double `$$` escapes Compose's variable interpolation.

**Style 2 — `command:` only override** (use when the image has empty `Entrypoint` and the lifecycle is driven by `command`, or when you need a setup step before the app starts):
```yaml
command:
  - sh
  - -c
  - "set -a && . /vault/secrets/credentials.env && set +a && <optional-setup> && exec <original-app> <args>"
```
The `<optional-setup>` (e.g., `pip install`, `migrate`) runs before exec. Only the final long-running app process needs `exec`.

**Where to find `<original-entrypoint>`**: inspect the image with `docker inspect <image> --format 'Entrypoint: {{.Config.Entrypoint}}\nCmd: {{.Config.Cmd}}'`. If `Entrypoint` is `[]` (empty) and `Cmd` is `[/start.sh]`, then `<original-entrypoint>` is `/start.sh`. If both are populated, the original execution is `entrypoint cmd...` — replicate exactly.

### Verification: PID 1 must be the application

After recreate, confirm:
```bash
docker exec <svc> /bin/sh -c 'tr "\0" " " < /proc/1/cmdline; echo'
# Should print the application binary, not "sh -c ..."

docker stop -t 10 <svc>
# Should complete in <2s, not the full 10s grace period
```

Failure of either check → the `exec` was missed somewhere.

**Note for non-root services**: applications that drop from root to a service user (e.g. postgres → uid 70) restrict `/proc/1/environ` to the process owner. A `docker exec` shell as root cannot read it. For these services, verify cred delivery via:
- Cross-container auth probe (sibling container connects with delivered cred)
- Server logs show no `password authentication failed` entries
- Application functions (e.g., postgres accepts connections, queries return data)

These signals together prove the cred reached the application even when /proc/1/environ is unreadable.

### Sub-pattern — credential-embedded URL rendering

Some applications consume connection strings (Postgres DSN, JDBC URL, AMQP URL, etc.) instead of separate credential env vars. For these, render the full URL via the Vault Agent template with the credential substituted in:

```
{{ with secret "secret/data/<service>/db" -}}
DATABASE_URL=postgresql://<user>:{{ .Data.data.password }}@<host>:<port>/<dbname>
{{- end }}
```

**Critical: URL-safe credential generation.** The credential embedded in a URL must NOT contain URL-special characters: `/`, `+`, `=`, `@`, `#`, `?`, `&`, etc. Use **hex** encoding for randomly-generated secrets that will live inside URLs:

```bash
# CORRECT — URL-safe (hex chars 0-9a-f only)
NEW_PASS=$(openssl rand -hex 22)   # 22 bytes → 44 hex chars

# WRONG — contains / + = which break DSN parsing
NEW_PASS=$(openssl rand -base64 32)
```

If the password contains `/`, the URL parser will treat it as a path separator and connect to the wrong host. This was an actual failure during BP2 (plane stack rotation): a base64 password caused `failed to resolve host 'plane'` errors because `postgresql://plane:<base64-with-slash>@plane-db/plane` was parsed as `host=<garbage>@plane-db`.

**When to prefer DSN render vs component env vars**: prefer component env vars (POSTGRES_HOST/PORT/USER/PASSWORD) if the application supports them — cleaner separation, simpler rotation, no URL-encoding gotchas. Use DSN render only when the app insists on a URL.

### ANTI-PATTERN — never display credential values in tool output

Never display credential values in tool output, even during diagnostics. Use hash-based equality verification only. If diagnosis appears to require value inspection, stop and surface for user decision. Pressure to debug quickly does not justify exposing credential values.

```bash
# WRONG
cat /vault/secrets/credentials.env
head -1 /vault/secrets/credentials.env
echo "$VAULT_PASS"
docker exec <container> env | grep PASSWORD

# RIGHT — hash-based comparison only
R=$(grep '^FIELD=' /path/to/file | cut -d= -f2- | tr -d '\n' | shasum -a 256 | awk '{print substr($1,1,12)}')
V=$(docker exec ... vault kv get -field=field path | shasum -a 256 | awk '{print substr($1,1,12)}')
[ "$R" = "$V" ] && echo "match" || echo "MISMATCH"
```

**Hashing methodology**: when extracting a value from a file or `printenv`, **always strip trailing newline** with `tr -d '\n'` or `printf '%s'` BEFORE hashing. `cat`, `printenv`, and pipe-extracted values include the line-terminator newline; the file's actual stored value does not. Hash mismatch from newline-inclusion is a false-positive trap that has tripped verification more than once.

Discovered: B.1 nextcloud-db rotation. Doctrine: rotate on any unintended exposure, even if conversation-local.

### ANTI-PATTERN — never use `--no-deps` with sidecar pattern

The Vault Agent sidecar IS a dependency of the main service (`depends_on: condition: service_completed_successfully`). Using `--no-deps` skips the sidecar, leaving the main container to fail at entrypoint when `/vault/secrets/credentials.env` doesn't exist.

```bash
# CORRECT
docker compose up -d <service>

# WRONG — skips sidecar, main container fails at source step
docker compose up -d --no-deps <service>
```

If you need to recreate ONLY the main service without the sidecar (e.g., to re-render with new Vault data after a rotation), use `docker compose restart <service>` (which doesn't recreate) AFTER manually triggering a sidecar render. But for any cred-rotation event that requires a full recreate, just let compose handle the dependency chain.

Discovered: B.1 first attempt (nextcloud-db). Same severity as the `exec` rule from A.5.

### KNOWN-LIMITATION — Colima/macOS bind-mount visibility delay

On Colima/macOS, host-bind mounts can take a moment to become visible inside a freshly-started container. If the main service starts immediately after the sidecar exits, the first `docker compose up` cycle may fail to see `/vault/secrets/credentials.env` even though the file is on the host.

`restart: unless-stopped` on the main service is sufficient mitigation: the container retries until the mount is visible (typically 1–16 retries on a busy macOS, succeeding within 1–2 minutes). No data loss because the data volume is independent.

Symptom in logs: `sh: .: line 0: can't open '/vault/secrets/credentials.env': No such file or directory` repeated several times before the application binary's normal startup logs appear.

If a service does NOT have `restart: unless-stopped`, recreate it once the sidecar has fully exited (5+ second gap). Or ensure the restart policy can tolerate transient first-start failures.

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
