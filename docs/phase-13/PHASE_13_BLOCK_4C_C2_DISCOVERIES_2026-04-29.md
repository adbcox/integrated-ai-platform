# Block 4.C — C2 Stop-and-Surface Discoveries

**Date:** 2026-04-29
**Block:** Phase 13 Block 4.C C2 (NetBox deployment)
**Status:** Seven discoveries; six resolved, one accepted-with-note.

## Index

1. **Port-conflict on host :8080** — NetBox host bind moved 8080 → 8084
   (8080 held by `dashboard.internal` Python uvicorn backend; 8081
   held by `mcpo-proxy` container). See **§1 below**.
2. **SSH-port-forward signal-vs-noise on lsof sweeps** — the
   diagnostic SSH session forwards ports and `lsof` reports them as
   held by `ssh`, a false positive that confuses the port sweep.
   See **§2 below**; captured as a C6 canonical pre-check follow-up.
3. **postgres:18-alpine breaking change** — netbox-postgres pinned
   back to upstream-faithful `postgres:17-alpine` after pg18 rejected
   the legacy `/var/lib/postgresql/data` mount layout and emitted
   `chmod: Operation not permitted` against `cap_drop:[ALL]`. See
   **§3 below**; captured as a C6 upstream-pinning follow-up.
4. **Healthcheck shells don't inherit PID-1 env** — when a service
   sources Vault-rendered env in its entrypoint (`set -a && . creds`)
   rather than declaring via compose `environment:`, the healthcheck
   command runs in a fresh shell that has no access to those vars.
   See **§4 below**; captured as a C6 healthcheck-pattern follow-up.
5. **Plan deviated from upstream entrypoint flow (`SKIP_SUPERUSER`)**
   — the original C2 plan specified manual `manage.py createsuperuser`
   plus separate API-token generation in C2.6/C2.7. Upstream's
   `docker-entrypoint.sh` already does both automatically when
   `SUPERUSER_*` env vars are present. Re-architected to use upstream
   flow: superuser+token created during entrypoint via Vault-rendered
   env. See **§5 below**; captured as a C6 upstream-flow-default
   follow-up.
6. **Housekeeping script path doesn't exist in netbox-docker 4.0.2**
   — the compose's `exec /opt/netbox/housekeeping.sh` failed with
   `exec: not found`; netbox-docker 4.0.2 invokes housekeeping as
   the Django management command `manage.py housekeeping` instead.
   Fixed with a `while sleep 86400` wrapper. See **§6 below**.
7. **Upstream's super_user.py prints partial token to stdout**
   — netbox-docker 4.0.2's bootstrap logs the V2 token *key* (last
   12 chars of token; the public identifier portion of the
   `Authorization: Bearer nbt_<key>.<secret>` form) to container
   stdout on creation. The *secret* portion is not logged, so this
   is not a credential leak in the strict sense, but it does
   surface a partial token identifier into routine `docker logs`
   output. **Accepted as-is** (not a deployment blocker; cannot
   be silenced without forking upstream). See **§7 below**.

These events all surfaced inside C2 (artifact authoring + first
three deployment attempts). Each contributes to a C6 closeout
follow-up — the pattern that emerges is "the canonical add-new-
service pre-check needs strengthening before it survives contact
with another deployment."

## §1 — Port-conflict on host :8080

### What happened

The NetBox compose file initially bound the NetBox web container
to `127.0.0.1:8080:8080`, matching the host port assumed in
`docs/phase-13/PHASE_13_BLOCK_4C_PLAN_2026-04-29.md` and the
operator-facing `docker/netbox/README.md`. Before SSH'ing to the
Mac Mini for stack bring-up (C2.5), a pre-flight `lsof` on the
host port revealed that `:8080` was already in use:

```
$ ssh admin@192.168.10.145 'lsof -nP -iTCP:8080 -sTCP:LISTEN'
COMMAND   PID  USER   FD   TYPE             DEVICE SIZE/OFF NODE NAME
Python  45891 admin    7u  IPv4 0x...                       TCP *:8080 (LISTEN)
```

`docker/caddy/Caddyfile:73-77` resolves this: `dashboard.internal`
reverse-proxies to `host.docker.internal:8080` — i.e. host port
8080 is already the operator-control-plane backend (Block 2.5),
and PID 45891 is its Python uvicorn process. NetBox would have
failed `bind: address already in use` on first `docker compose up`.

### Resolution

Per operator approval (2026-04-29):

1. **Verified 8081 was occupied** by `mcpo-proxy` Docker
   container (`0.0.0.0:8081->8081/tcp`) — surfaced rather than
   auto-picked.
2. **Swept 80xx band**, finding 8084, 8087, 8089, 8095 free.
3. **Selected 8084** (closest to documented 8080, no semantic
   clash with adjacent services 8082 headscale / 8083 vaultwarden
   / 8085 nextcloud / 8086 control-plane).
4. **Updated three artifacts**:
   - `docker/netbox/docker-compose.yml:237-240` — host bind
     `127.0.0.1:8084:8080` (container side stays 8080 for the
     healthcheck `curl http://localhost:8080/login/`).
   - `docker/caddy/Caddyfile` — appended `netbox.internal` block
     in the Platform Layer (after `homarr.internal`),
     `reverse_proxy host.docker.internal:8084`.
   - `docker/netbox/README.md` — Caddy-route line and topology
     diagram updated to 8084.

## §2 — SSH-port-forward signal-vs-noise on lsof sweeps

While sweeping 8081-8095 to pick a free port, `lsof` consistently
reported an `ssh` process holding many of the candidate ports
(`8083`, `8085`, `8086`, `8091`, `8092`, `8093`, `8094` all showed
`host=ssh`). This is **noise from the diagnostic SSH session
itself**, not real listeners on the Mac Mini.

The signal that distinguishes a real occupant from an SSH-forward
artifact is **presence in `docker ps --format "{{.Names}} {{.Ports}}" | grep ":<port>->"`**.
A row where the docker-ps lookup yields a container name (e.g.
`vaultwarden`, `mcpo-proxy`, `mcp-filesystem-remote`) is a real
host-side bind. A row where docker-ps says `none` and only `lsof`
shows `ssh` is the operator's own SSH session forwarding through.

The pre-flight script must therefore consult **both** signals and
ignore `ssh`-only matches.

### C6 follow-up registered (port-conflict pre-check)

A canonical pre-deployment port-conflict pre-check is registered
as a C6 closeout follow-up. It must:

- Take `<host-port>` as input.
- Run `lsof -nP -iTCP:<port> -sTCP:LISTEN` on the target host
  via SSH **and** `docker ps --format '{{.Names}} {{.Ports}}' | grep ':<port>->'`.
- Return CLEAR only if both signals agree the port is free
  (no listener AND no docker mapping), filtering out any `ssh`
  COMMAND in the lsof result as caller-induced noise.
- Output the resolving container name (or non-docker process)
  if occupied, so the next-port suggestion is informed.

This avoids both halves of the failure mode encountered here:
the original 8080 surprise (no pre-check at all) and the false
positive on the SSH-noise rows during recovery (lsof alone
mis-flagged free ports as occupied).

## §3 — postgres:18-alpine breaking change

### What happened

The C2.5 first-attempt `docker compose up -d` started the four
Vault Agent sidecars (which all rendered cleanly and exited 0 with
secrets in place), brought up the two Valkey containers (healthy),
but `netbox-postgres` entered a restart loop. Logs showed:

```
chmod: /var/lib/postgresql/18/docker: Operation not permitted
chmod: /var/run/postgresql: Operation not permitted
Error: in 18+, these Docker images are configured to store database
       data in a format which is compatible with "pg_ctlcluster"
       (specifically, using major-version-specific directory names).
       ...
       Counter to that, there appears to be PostgreSQL data in:
         /var/lib/postgresql/data (unused mount/volume)
```

Two failures in one stack:

1. `postgres:18-alpine` introduced a breaking change to its data
   layout. It expects `/var/lib/postgresql` as the volume mount
   root and stores per-major-version data under
   `/var/lib/postgresql/<major>/docker/` (so `pg_upgrade --link`
   can run cleanly). The compose file mounted at the legacy
   `/var/lib/postgresql/data` path. The image refused to use it.
2. The `chmod: Operation not permitted` errors against `cap_drop:[ALL]`
   suggest pg18's init script needs file-mode operations that even
   our `cap_add: [CHOWN, SETUID, SETGID, DAC_OVERRIDE]` did not
   permit (specifically the `chmod` on `/var/run/postgresql`).
   This second failure is downstream of the first — the legacy
   path was the real blocker — but it indicates pg18 init has a
   different cap surface than pg17.

The cascade was: `netbox-postgres` unhealthy →
`netbox-redis`/`netbox-redis-cache` healthy (independent) →
`netbox` waiting on `netbox-postgres` healthy → "dependency failed
to start" terminal error.

### Resolution

Per operator approval (2026-04-29, Path A):

1. **Reverted to upstream-faithful `postgres:17-alpine`.**
   netbox-docker 4.0.2 (the upstream release used here) pins pg17,
   not pg18. The C1 audit had captured pg18 as a deliberate
   "platform fresher than upstream" choice; reverted to the
   upstream pin per the doctrine principle of upstream-faithful
   where possible.
2. **Stack torn down with `docker compose down -v`** (note `-v`
   to drop the partially-initialised `netbox-postgres-data` volume
   so pg17 inits cleanly on next bring-up). All vault-agent sinks
   under `/Users/admin/.vault-agent-secrets/netbox*/` are
   preserved; only the database volume was removed.
3. **Updated three artifacts**:
   - `docker/netbox/docker-compose.yml` — `postgres:18-alpine`
     → `postgres:17-alpine`; expanded the head comment to record
     the pivot and link this discoveries doc.
   - `config/service-registry.yaml` — netbox-postgres `image:`
     and `notes:` updated.
   - This doc — added §3.

### C6 follow-up registered (upstream pinning)

A doctrine-level rule is registered as a C6 closeout follow-up:

> Pin database major versions to upstream-faithful values in the
> canonical add-new-service pattern. Deviating from upstream
> (e.g., pg18 when netbox-docker pins pg17) needs explicit
> doctrine-level rationale, not silent advance. The C1 audit
> should default-pin to whatever the upstream image
> pinning chooses, and any deviation must be flagged for explicit
> approval rather than carried as a silent platform-modernisation
> choice.

This doesn't preclude future modernisation — it requires that
modernisation be a first-class decision, not an artefact of
"pick the latest stable" defaults applied during artifact
authoring.

## §4 — Healthcheck shells don't inherit PID-1 env

### What happened

After the pg17 pivot, `netbox-postgres` became healthy as expected,
but `netbox-redis` and `netbox-redis-cache` reported `unhealthy`
status even though the Valkey processes themselves were happily
accepting connections (logs showed `Ready to accept connections
tcp` and `requirepass` was applied via the entrypoint).

Root cause: the Valkey healthcheck was

```yaml
test: ["CMD-SHELL", "[ $$(valkey-cli --pass \"$$REDIS_PASSWORD\" ping) = 'PONG' ]"]
```

Manual diagnostic from inside the container revealed
`echo PASS_LEN=${#REDIS_PASSWORD}` returned `PASS_LEN=0` — i.e.
the env var was empty in the healthcheck shell, even though the
valkey-server process (PID 1) had it correctly set via the
entrypoint's `set -a && . /vault/secrets/credentials.env && set +a`.

Why: Docker `HEALTHCHECK` (which compose's `healthcheck.test:` becomes)
runs as `docker exec`-equivalent — a fresh shell inside the container
that inherits **only the env declared via compose `environment:`**,
not PID-1's runtime env. Since the platform's Vault doctrine forbids
declaring credentials via `environment:` (must come from rendered
credentials.env), the healthcheck shell sees an empty
`REDIS_PASSWORD`, AUTH fails with `WRONGPASS`, and the healthcheck
flips to unhealthy on a process that's perfectly healthy.

### Resolution

Healthcheck command updated to source the rendered credentials.env
itself before invoking valkey-cli:

```yaml
test: ["CMD-SHELL", ". /vault/secrets/credentials.env && [ \"$$(valkey-cli --pass \"$$REDIS_PASSWORD\" ping)\" = 'PONG' ]"]
```

This works because the `/vault/secrets/` mount is already present
on the Valkey containers (read-only, owned by the vault-agent
sidecar's render). The healthcheck shell can read it.

Same pattern applied to both Valkey containers (netbox-redis and
netbox-redis-cache). Postgres healthcheck is unaffected because
its inputs (`POSTGRES_USER`, `POSTGRES_DB`) come from compose
`environment:` (declared, inherited) and `pg_isready` doesn't
need a password.

### C6 follow-up registered (healthcheck pattern)

> Doctrine for the canonical add-new-service pattern: any service
> that sources credentials from a Vault-rendered env file in its
> entrypoint must apply the same source step in its healthcheck
> command. Healthcheck shells do not inherit PID-1 env. The
> alternative — declaring secrets via compose `environment:` so
> they reach the healthcheck shell — violates the platform secrets
> doctrine and is forbidden. Source the credentials.env in the
> healthcheck.

## §5 — Plan deviated from upstream entrypoint flow (SKIP_SUPERUSER)

### What happened

The original C2 plan specified two manual post-deployment steps:

- **C2.6**: SSH to Mac Mini, fetch `secret/netbox/admin#password`
  from Vault, pipe through stdin to a `manage.py shell` heredoc
  that creates the Django superuser with `make_password`-hashed
  credentials.
- **C2.7**: invoke `manage.py shell` again to fetch-or-create the
  user's `Token`, write the resulting key to
  `secret/netbox/api_token#token`.

To support this manual flow, the compose set `SKIP_SUPERUSER: "true"`
on the netbox container — instructing upstream's
`docker-entrypoint.sh` *not* to run its built-in superuser bootstrap.

After the third C2.5 deployment attempt landed all 7 containers,
a diagnostic shell against the netbox container showed
`USER_EXISTS: False`, and the bootstrap log line
`↩️ Skip creating the superuser` confirmed the
`SKIP_SUPERUSER` flag had silenced upstream's flow.

Inspection of `/opt/netbox/super_user.py` (the script upstream's
entrypoint runs unless `SKIP_SUPERUSER=true`) revealed it already
handles everything the manual C2.6+C2.7 flow was meant to do:

```python
# super_user.py reads from env (with /run/secrets/* fallback):
SUPERUSER_NAME       (default "admin")
SUPERUSER_EMAIL      (default "admin@example.com")
SUPERUSER_PASSWORD   (default "admin")
SUPERUSER_API_TOKEN  (default a 40-char hex string)

# Creates user only if not present, using create_superuser().
# Creates Token alongside, writing the SUPERUSER_API_TOKEN value
# directly (V2 token version).
```

The original plan was authored without this knowledge; it copied
the manual-bootstrap shape from earlier services in the platform
that don't have an upstream auto-bootstrap.

### Resolution

Per operator approval (2026-04-29, Option B):

1. **Provisioning script extended**:
   - `secret/netbox/admin` now carries three fields: `password`
     (existing, random), `username` ("admin"), `email`
     ("admin@netbox.internal" — `<service>.internal` is the
     platform addressing convention; in-domain so any
     entrypoint-emitted email is internally routable rather than
     bouncing off `example.com`).
   - `secret/netbox/api_token#token` migrates from a literal
     `"PLACEHOLDER_REPLACE_IN_C2_7"` placeholder to a 40-char
     random hex token (matching `super_user.py`'s default token
     width). `provision_random_secret` was extended to treat
     values starting with `PLACEHOLDER_` as absent so the
     migration completes idempotently on re-run.
   - Two new helpers added: `vault_kv_patch_stdin` (uses
     `vault kv patch` to update a single field on an existing
     KVv2 path without disturbing other fields) and
     `provision_literal_secret` (idempotent literal-value
     provisioning, e.g., for username/email).

2. **credentials.env.tmpl extended** to render
   `SUPERUSER_NAME`, `SUPERUSER_EMAIL`, `SUPERUSER_API_TOKEN` from
   the Vault paths above (in addition to the pre-existing
   `SUPERUSER_PASSWORD`).

3. **Compose changed**: `SKIP_SUPERUSER: "true"` → `"false"` on
   the netbox container (worker and housekeeping retain
   `SKIP_SUPERUSER: "true"` because those containers don't run
   the bootstrap flow). Comment expanded to record that the
   upstream entrypoint handles bootstrap automatically.

4. **Vault policy tightened**: `secret/data/netbox/api_token`
   capabilities `["create", "update", "read"]` →
   `["read"]`. The api_token is now provisioned by the operator
   script (root token), not the netbox AppRole; AppRole only
   needs read.

5. **Verification path simplifies**: instead of running
   manage.py heredocs in C2.6/C2.7, post-redeploy verification
   asserts `USER_EXISTS: True` and `TOKEN_EXISTS: True` via a
   diagnostic shell, and the API-token round-trip uses the value
   already in Vault. The original plan's C2.6 + C2.7 collapse to
   "verify the entrypoint did the right thing."

### C6 follow-up registered (upstream-flow default)

> Doctrine for the canonical add-new-service pattern: when an
> upstream image's entrypoint already handles bootstrap concerns
> (superuser creation, token generation, schema seeding,
> migrations), the canonical pattern's default MUST be "use the
> upstream entrypoint flow." Manual `manage.py`-style post-hoc
> bootstrap is acceptable only when the operator has documented
> a specific reason the upstream flow is unsuitable
> (e.g., upstream flow doesn't support the platform's secret
> source, or the upstream flow does too much for the deployment
> shape). Future C1 audits should identify upstream entrypoint
> behaviour as a first-class question and default to using it.

## §6 — Housekeeping script path doesn't exist in netbox-docker 4.0.2

### What happened

After the third C2.5 deployment landed all 7 containers,
`netbox-housekeeping` immediately entered a restart loop with:

```
/bin/sh: 1: exec: /opt/netbox/housekeeping.sh: not found
```

`docker exec netbox find / -name "housekeeping*"` returned only
`/opt/netbox/netbox/extras/management/commands/housekeeping.py`
— the Django management command. There is no
`/opt/netbox/housekeeping.sh` script in netbox-docker 4.0.2.
`/opt/netbox/` ships only `docker-entrypoint.sh`,
`launch-netbox.sh`, and `super_user.py`.

Earlier netbox-docker releases (pre-4.0) shipped a
`housekeeping.sh` shell script. This was removed in favour of
running the Django command directly, with operators wrapping it
in their own scheduling layer (cron/systemd timer). The original
C2 plan referenced the older path without verifying the
release-current shape.

### Resolution

Compose `command:` updated to:

```sh
set -a && . /vault/secrets/credentials.env && set +a && \
  cd /opt/netbox/netbox && \
  while true; do
    /opt/netbox/venv/bin/python manage.py housekeeping
    sleep 86400
  done
```

`while true; do … sleep 86400; done` runs the housekeeping
command every 24 hours. The container stays alive between
runs (sleeping shell), so `restart: unless-stopped` semantics
hold. The healthcheck (`grep -q housekeeping || exit 0`) is a
no-op (always returns 0) — the container's value is "is the
wrapping shell alive looping," and `restart` covers crashes.

### Implicit C6 follow-up (covered by §5's upstream-flow rule)

This same defect — referencing a script path that doesn't exist
in the release-current upstream image — is exactly what §5's
"default to upstream flow" follow-up addresses. The C1 audit
should verify "what does the entrypoint expect" and "what
ancillary files exist" against the actual pinned image, not
against assumed conventions from earlier releases.

## §7 — Upstream's super_user.py prints partial token to stdout

### What happened

After the fourth (and successful) deployment, `docker logs netbox`
contained the line:

```
💡 Superuser Username: admin, E-Mail: admin@netbox.internal,
   API Token: 08aADokGMxrG (use with 'Bearer nbt_08aADokGMxrG.<Your token>')
```

Reading `super_user.py` (the script upstream's entrypoint runs):

```python
t = Token.objects.create(user=u, token=su_api_token, version=TokenVersionChoices.V2)
msg = f"💡 Superuser Username: {su_name}, E-Mail: {su_email}, API Token: {t} (use with '{t.get_auth_header_prefix()}<Your token>')"
print(msg)
```

`{t}` (the str of a Token instance) renders the Token's **key**
attribute, which in V2 tokens is the *public identifier* portion
of the auth header (`Bearer nbt_<key>.<secret>`). The **secret**
portion is masked as the literal string `<Your token>` and never
goes through stdout.

Strictly: this is not a credential leak — knowing the key without
the secret does not authenticate. But it does surface a partial
token identifier into routine `docker logs` output that goes to
host disk via Docker's json-file logger.

### Resolution

**Accepted as-is.** Reasoning:

1. The leaked portion (the key) is the half that's transmitted
   in plaintext on every API request anyway — anyone who can
   sniff in-cluster traffic already sees it. The secret half is
   the one that matters, and that stays in Vault.
2. Suppressing this print would require either
   (a) forking netbox-docker (over-the-top maintenance burden
   for a partial-identifier print), or
   (b) post-bootstrap log redaction at the platform layer
   (additive complexity for marginal value).
3. The platform's secrets doctrine ("display of credential values
   during diagnostics is forbidden") was authored against
   credential *secrets*, which this is not.

If future doctrine review wishes to broaden "credential value"
to include public token identifiers, the resolution is to swap
to a custom `super_user.py` mounted in via volume override
(thinner intervention than a fork). Captured as a *potential*
future hardening item; not currently required.

### No C6 follow-up registered

The decision is "accept as-is per the reasoning above"; no
canonical-pattern change is needed. Surfacing here for
auditability — the next operator reading `docker logs netbox`
will see this line and should not be surprised by it.

---

## Discovery #13: Plane homepage_token diverges between memory file and Vault — both valid, different tokens

**Surfaced by:** C4 pre-flight memory hygiene check (per plan C4.2).
**Severity:** Doctrine-relevant (plaintext credential in memory file used by an active script).
**Resolution:** A1 + scope-probe path; Vault token confirmed admin write scope; memory plaintext redacted to Vault path reference; C6 follow-up registered to revoke memory token via Plane UI.

### What happened

Plan C4.2 specified a pre-flight check before running the back-fill:

> Read the plaintext Plane token at `~/.claude/projects/.../memory/plane_deployment.md`,
> compare hash to Vault copy at `secret/plane/api`, and if they match,
> redact the memory file before the back-fill runs. **If they diverge,
> stop and surface — do NOT auto-rotate.**

Hash comparison (sha256, first 12 hex chars):

| Source                                              | Hash prefix     |
|-----------------------------------------------------|-----------------|
| Memory file plaintext (line 14, original)           | `4d83dff62161`  |
| Vault `secret/plane/api#homepage_token`             | `b90c7b634be7`  |

They **do not match**. Two distinct tokens, both currently valid
against the same workspace/project (read probes returned 200 with
the same issue and label inventories).

This was unexpected. The memory file was written 2026-04-25 during
Plane CE deployment; Vault was the canonical store from day 1. The
divergence implies either a token rotation that updated Vault but
not memory, or a second token issued at some point that landed in
memory but was never reconciled with Vault.

### Resolution path (A1 + scope-probe, operator-approved)

**Step 1 — Read probes against both tokens (no writes):**

```
GET /api/v1/workspaces/iap/projects/<id>/issues/?per_page=1   → 200 (total=604)
GET /api/v1/workspaces/iap/projects/<id>/labels/              → 200 (count=64)
```

Both tokens passed read probes. Identical inventories returned.

**Step 2 — Write-scope probe on Vault token only (PATCH + restore on a label description):**

```
PATCH /api/v1/.../labels/<id>/  (description="<probe>")  → 200
PATCH /api/v1/.../labels/<id>/  (description="<original>") → 200
```

Vault `secret/plane/api#homepage_token` confirmed **admin write scope**.

**Step 3 — Path A1 executed (Vault token has admin write scope):**

1. Back-fill script (`scripts/backfill-plane-labels.py`) reads token via
   `docker exec vault-server vault kv get -field=homepage_token secret/plane/api`
   — never the memory file.
2. Memory file `plane_deployment.md` line 14 redacted to:
   `Token reference: secret/plane/api#homepage_token (redacted from plaintext on 2026-04-29 per Block 4.C C4 pre-flight)`
3. Note added to memory file recording the hash divergence (the formerly-plaintext
   token in memory was a *different valid token*, not a stale copy of the Vault one).

A2 (fall back to memory plaintext) was **explicitly forbidden** by operator —
that would leave a plaintext credential in a file consumed by an active
script, doctrine violation.

A3 (provision a fresh dedicated `secret/plane/api#backfill_token` via Plane UI)
was the alternative path if A1's scope probe had failed. It did not fail,
so A3 was not needed.

### Hash-only verification

No token value was displayed at any point during the probe or
redaction work. Tokens were:
- Read from Vault via subprocess `vault kv get -field=...` (captured stdout, held as Python str only).
- Read from memory file by Python (held as str only).
- Hashed via `hashlib.sha256(...).hexdigest()[:12]` and only the hash prefix surfaced.
- Used as `X-Api-Key` header value via the existing `PlaneAPI` client.

### C6 follow-up #9

> Revoke the memory-file Plane token via Plane UI. It is a different
> token from the canonical Vault token, no longer needed for any
> automation, and its revocation tightens the credential surface.
> Reference: hash `4d83dff62161`. (Cannot be revoked from the API
> without admin access to the token-management UI; flagged for
> manual operator action during C6 closeout.)

### Lesson for future memory hygiene

Memory files that store credentials inline are **load-bearing
surfaces**. Even when the platform's canonical store is Vault,
a plaintext copy in memory creates:
- A second copy that can drift (this case).
- A second copy that can be consumed by automation that bypasses
  Vault (this case nearly happened — the plan originally said
  "read token from memory file" before the doctrine review).

**Forward doctrine:** memory files must reference Vault paths, not
inline credential values. Any inline credential in memory is a
hygiene defect, regardless of whether it is currently in use.
This is registered as platform doctrine going forward; the C2/C3/C4
sweep redacted the only known instance.
