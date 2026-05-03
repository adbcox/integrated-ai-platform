# Vault Agent sidecar pattern — durable doctrine

The canonical pattern for delivering Vault-backed credentials to
container workloads on this platform: **AppRole-authenticated Vault
Agent sidecar renders a templated env file to a shared volume; the
consumer mounts it read-only and sources it at startup.** Credentials
never live in tracked files, never in repo history, never in chat
output, never in `docker inspect` output.

Sibling chronicles:
- `integration-audit-doctrine.md` — Finding 6 (D-17-38 hash-only
  verification rule + `/proc/1/environ` redacted-grep sub-doctrine,
  load-bearing for the verification section below)
- `opnsense-dns-authority.md` — DNS substrate the consumer-side
  URL form depends on (container DNS, not `*.internal` from inside
  the Docker network — D-17-38 root cause)

---

## What this pattern solves

Three failure modes that other delivery shapes don't close:

1. **Credentials in repo / on disk.** `.env` files, Docker
   `environment:` keys, build-time `ARG`s — all leave traces in
   git, image layers, or `docker inspect`. Vault Agent renders to
   a tmpfs-backed volume; nothing is committed, nothing is baked
   into the image.
2. **Credentials in chat / log output.** A pattern that requires
   the operator to copy a value from one terminal to another (or
   from chat to a file) is a credential-display pattern by
   construction. Vault Agent runs without operator intervention;
   the operator never sees the value.
3. **Credential drift between Vault and consumer.** A consumer
   that reads from a static file goes stale on rotation. Vault
   Agent re-renders on every consumer restart; rotation is a
   Vault-side write + consumer restart, no consumer config
   change.

This pattern is the default for any container that consumes a
credential governed by Vault. Exceptions are enumerated in "When
NOT to use this pattern" below.

---

## Architecture

```
[Provision time, once per service]

  operator → scripts/lib/vault-admin-token.sh
                  │ (admin token, never echoed)
                  ↓
            scripts/provision-<service>.sh
                  │ writes policy + creates AppRole
                  ↓
            ~/.vault-approle/<service>/role-id
            ~/.vault-approle/<service>/secret-id

[Runtime, on every consumer start]

  [Vault Agent sidecar]                    [Consumer container]
        │                                          │
        ├── reads role-id + secret-id              │
        ├── AppRole auth → Vault Server            │
        ├── token sink → /vault/secrets/.vault-token
        ├── reads policy-scoped paths              │
        │       (e.g. secret/data/arr/sonarr)      │
        ├── renders template →                     │
        │   /vault/secrets/credentials.env (0444)  │
        └── exit_after_auth = true                 │
                          │                        │
                  [shared volume: /vault/secrets]  │
                          │                        │
                          └────── mounts ro ──────→┤
                                                   │
                                          sources credentials.env
                                          at entrypoint
```

`exit_after_auth = true` is intentional: the sidecar's job is
one-shot delivery, not long-running token renewal. Consumer
restart is the rotation primitive.

---

## Required artifacts per service

Every service that adopts this pattern lands the same five files
in the same five locations. The recurring shape across the N=5
worked examples (dashboard, buildarr, bazarr, scraparr,
cleanuparr) is byte-identical for the agent.hcl and structurally
identical for the others.

### 1. Vault policy — `config/vault-policies/<service>-policy.hcl`

Policy grants `read` capability on the specific
`secret/data/<service-domain>/<resource>` paths the consumer
needs, and nothing else.

```hcl
path "secret/data/arr/sonarr" {
  capabilities = ["read"]
}
path "secret/data/arr/radarr" {
  capabilities = ["read"]
}
```

Keep policies tight. A consumer that reads two upstream APIs
gets two paths, not a wildcard. If the consumer needs a shared
platform path (e.g. `secret/data/qnap/admin` for the dashboard
QNAP probe), add it explicitly — never via glob.

### 2. Agent config — `docker/vault-agent-<service>/agent.hcl`

The agent.hcl is byte-identical across all worked examples.
Per-service variation lives in the template file (next), not
here.

```hcl
pid_file = "/tmp/agent.pid"

vault {
  address = "http://vault-server:8200"
}

auto_auth {
  method "approle" {
    mount_path = "auth/approle"
    config = {
      role_id_file_path                   = "/vault/approle/role-id"
      secret_id_file_path                 = "/vault/approle/secret-id"
      remove_secret_id_file_after_reading = false
    }
  }
  sink "file" {
    config = {
      path = "/vault/secrets/.vault-token"
    }
  }
}

template {
  source      = "/vault/agent-config/credentials.env.tmpl"
  destination = "/vault/secrets/credentials.env"
  perms       = "0444"
}

exit_after_auth = true
```

`remove_secret_id_file_after_reading = false` is required: the
sidecar needs to re-read the secret-id on every restart.
Removing it on first read breaks rotation-by-restart.

### 3. Template — `docker/vault-agent-<service>/credentials.env.tmpl`

The template is the only per-service file with real variation.
Shape:

```
{{ with secret "secret/data/<domain>/<resource>" -}}
<VARNAME>={{ .Data.data.<field> }}
{{- end }}
```

One `{{ with secret ... }}` block per Vault path the policy
grants, rendering the field(s) the consumer expects. Multiple
blocks compose into one env file:

```
{{ with secret "secret/data/arr/sonarr" -}}
SONARR_API_KEY={{ .Data.data.api_key }}
{{- end }}
{{ with secret "secret/data/arr/radarr" -}}
RADARR_API_KEY={{ .Data.data.api_key }}
{{- end }}
```

The KV v2 `.Data.data.<field>` path is correct (KV v1 would be
`.Data.<field>`). Platform standardized on KV v2 at Phase 15
KV-rebuild close.

### 4. Provision script — `scripts/provision-<service>.sh`

Idempotent shell script that:

1. Sources `scripts/lib/vault-admin-token.sh` to get an admin
   token (never carries the token literal itself — see "AppRole
   bootstrap" below).
2. Writes the policy via `vault policy write`.
3. Creates the AppRole referencing the policy.
4. Reads the role-id + secret-id and writes them to
   `~/.vault-approle/<service>/role-id` and
   `~/.vault-approle/<service>/secret-id` (mode 0600).

The script is operator-run at deploy time, once per host. Re-runs
are safe (policy and AppRole writes overwrite cleanly).

### 5. Compose entry — sidecar + consumer + shared volume

```yaml
services:
  vault-agent-<service>:
    image: hashicorp/vault:<pinned>
    command: vault agent -config=/vault/agent-config/agent.hcl
    volumes:
      - ./docker/vault-agent-<service>:/vault/agent-config:ro
      - ~/.vault-approle/<service>:/vault/approle:ro
      - <service>-secrets:/vault/secrets
    networks: [...]
    cap_drop: [ALL]
    security_opt: [no-new-privileges:true]

  <service>:
    image: <consumer-image>
    depends_on:
      vault-agent-<service>:
        condition: service_completed_successfully
    volumes:
      - <service>-secrets:/vault/secrets:ro
    # consumer entrypoint sources /vault/secrets/credentials.env

volumes:
  <service>-secrets:
```

Two non-negotiables here:

- **`condition: service_completed_successfully`** on the depends_on.
  The sidecar must exit cleanly (after rendering) before the
  consumer starts. `exit_after_auth = true` in agent.hcl makes
  the sidecar exit as soon as the template renders;
  `service_completed_successfully` makes compose wait for that
  exit before starting the consumer. Without this, the consumer
  races the render and reads an empty/missing file.
- **`:ro` on the consumer mount.** The consumer never writes to
  `/vault/secrets`. Read-only enforces this; a misbehaving
  consumer can't corrupt the shared volume.

---

## AppRole bootstrap flow

`scripts/lib/vault-admin-token.sh` is sourced (not executed) by
every provision script. Its responsibilities:

1. Resolve an admin token from a secure source — operator's
   post-rebuild Shamir-unwrapped init token, or a `$VAULT_TOKEN`
   override for CI / re-runs.
2. Validate the token against Vault before returning it (a
   stale token here would cascade into provision-script failures
   that look like permissions issues).
3. Export it as `VAULT_TOKEN` to the calling shell. Never
   echoed to stdout, never written to a file the script doesn't
   own.

Provision scripts never carry the admin token literal because:

- Embedding the token in a script puts it on disk in cleartext.
- Passing it as an env var into the script transcript leaks it
  into shell history.
- Re-using a token across services means a stale token in one
  script affects all services. The helper revalidates per-call.

The flow is: helper validates admin token → provision script
uses it for `vault policy write` + `vault write auth/approle/role/...`
→ script reads the resulting role-id + secret-id → renders them
to `~/.vault-approle/<service>/`. The Vault Agent sidecar
reads those files at boot. No further admin-token use.

---

## Hash-only verification

All credential verification on this platform follows the D-17-38
Finding 6 hash-only rule. Two operations matter for this pattern:

### Comparing credentials between substrates

Use `sha256[:12]` fingerprints. Compare fingerprints, never
values:

```bash
# Vault side (server, never piped to chat)
vault kv get -field=api_key secret/arr/sonarr | sha256sum | cut -c1-12

# Service side (running container, never piped to chat)
docker exec sonarr cat /config/config.xml \
  | grep -oE '<ApiKey>[^<]+</ApiKey>' | sed 's/<[^>]*>//g' \
  | sha256sum | cut -c1-12
```

Equal fingerprints = equal credentials. Unequal = drift, surface
back. The values themselves stay on the host they live on.

### Checking credential presence in a running container

The image-baked `Config.Env` is *not* the runtime PID 1 environ
when the entrypoint sources a secrets file (D-17-26 sub-
doctrine). The correct check reads `/proc/1/environ` — but
`/proc/1/environ` reads emit values, so the read MUST be piped
through a redactor:

```bash
# Presence-only (correct):
docker exec <consumer> sh -c 'tr "\0" "\n" < /proc/1/environ' \
  | grep ^SONARR_API_KEY= \
  | sed 's/=.*/=<set>/'

# Count-only (also correct — emits 0 or 1):
docker exec <consumer> sh -c 'tr "\0" "\n" < /proc/1/environ' \
  | grep -c ^SONARR_API_KEY=
```

The bare-grep form `grep -z 'VAR_NAME=' /proc/1/environ` emits
the value and is a credential-display incident even when "just
diagnosing." This was a D-17-38 near-miss codified into doctrine
specifically to prevent the diagnostic-leak failure mode.

### URL drift as a credential failure

A URL value in Vault is part of the credential record, not
metadata. A URL that resolves on the host but not from inside
the consumer container is a broken credential — D-17-38's root
cause was Vault holding `<host>.<lan-tld>:<port>` URLs that
didn't resolve from inside the dashboard container's Docker
network. The canonical form for consumer-internal URLs is
`http://<container-name>:<port>` (Docker DNS), not
`http://<host>.<lan-tld>:<port>`. Verify URL form during
provisioning, not after the consumer fails to authenticate.

---

## Failure modes observed across the worked examples

These are real failure modes from the D-17-38 / D-17-26 / D-17-44
chronicles, not speculative. Each new service applying this
pattern should check against this list during deploy.

1. **Sidecar-consumer startup race.** Without
   `condition: service_completed_successfully` (or a wait-for-
   render in the consumer entrypoint), the consumer starts
   before `credentials.env` exists. Consumer crashes with "no
   such file" or "empty value." Fix: explicit dependency
   condition; never `--no-deps` with this pattern (sidecar IS a
   dependency).
2. **Image-baked `Config.Env` ≠ runtime environ (D-17-26).**
   `docker exec env` shows what the image declared, not what
   PID 1 actually sources. A credential variable can appear
   missing in `docker inspect` while being correctly set at
   runtime, or vice versa. Always check `/proc/1/environ` (with
   redactor), never `docker exec env`, when verifying credential
   delivery.
3. **URL drift between Vault and consumer reachability
   (D-17-38).** Vault holds a URL form (e.g.
   `<host>.<lan-tld>:<port>`) that resolves on the host but not
   from inside the Docker network. Health checks fail with
   misleading errors (DNS, TLS, auth — all downstream of the
   actual cause). Fix: store consumer-internal URLs as
   `http://<container-name>:<port>`; reserve `*.internal` URLs
   for host-side or operator-side use.
4. **Credential-source authority inversion (D-17-38).** When a
   long-running service generates its own credential (e.g. arr-
   stack `<ApiKey>` in `/config/config.xml`), the live service
   is canonical. Reading Vault and writing back to the service
   creates drift. Direction is service → Vault, never the
   reverse, for service-generated credentials.
5. **Diagnostic credential display.** Bare grep of
   `/proc/1/environ` during incident response leaks the value
   into the operator's terminal scrollback. The redactor pipe
   is mandatory even when the operator is the only audience —
   scrollback is an artifact, and credential-display incidents
   are evaluated by the artifact, not the intent.
6. **Stale role-id / secret-id after Vault rebuild.** Vault data
   loss (Phase 15 KV-loss event) invalidates all AppRole
   secret-ids. Files in `~/.vault-approle/<service>/` are now
   pointing at a non-existent role. Fix: re-run
   `provision-<service>.sh` after any Vault rebuild.

---

## When NOT to use this pattern

- **Frontend-only services** (e.g. plane-web, dashboard static
  assets) that don't read credentials at startup. No sidecar
  needed; no env file needed.
- **Services managed outside docker-compose** (Obot-managed
  shims per CLAUDE.md D#30 — `mcp-docker-remote`,
  `sms1obot-mcp-server`, `sms1obot-mcp-server-shim`). The compose-
  level depends_on primitive doesn't apply; these services'
  credential delivery is governed by Obot's lifecycle, not this
  pattern.
- **LLM-routing tokens consumed by litellm.** litellm has its
  own config substrate; routing through Vault Agent would
  duplicate without benefit. Local-only LLM routes (post Phase
  13.5 cloud-LLM deprecation) don't need credentials at all.
- **Build-time secrets** (image-build args, CI tokens). These
  aren't runtime credentials; they belong in the CI substrate's
  secret store, not in this pattern.

When in doubt, the test is: does the service read this
credential at runtime, every time it starts, on this platform?
If yes → this pattern. If no → one of the above.

---

## Cross-reference

- `docs/runbooks/add-new-service.md` — operational runbook for
  adding a service that uses this pattern. The runbook walks the
  five-artifact checklist; this chronicle explains why the
  artifacts have the shape they do.
- `docs/architecture-facts/integration-audit-doctrine.md`
  Finding 6 — full D-17-38 chronicle including the hash-only
  rule, redactor sub-doctrine, URL-form rule, and credential-
  source-authority rule.
- `docs/runbooks/rotate-credentials.md` — rotation flow uses
  this pattern's "restart consumer = re-render" property.

---

## Why this lives in `architecture-facts/`

The sidecar pattern outlives any single deliverable. Every
credential-consuming service on the platform follows it; every
future arr-stack expansion (Lidarr, Autobrr, Profilarr) will
apply it; every cross-deliverable audit relies on it being
canonical. Phase docs reference *events* (a service was added,
a rotation happened); architecture-facts reference *durable
posture* (this is how all such services deliver credentials).

The five-artifact shape was abstracted from N=5 worked examples
(dashboard, buildarr, bazarr, scraparr, cleanuparr) at D-17-53
WP-04 / Goose Session 4, with the credential-display anti-
pattern in the verification section corrected to match D-17-38
Finding 6 sub-doctrine before commit.
