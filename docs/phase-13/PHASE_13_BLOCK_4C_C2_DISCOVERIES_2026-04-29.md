# Block 4.C — C2 Stop-and-Surface Discoveries

**Date:** 2026-04-29
**Block:** Phase 13 Block 4.C C2 (NetBox deployment)
**Status:** Three discoveries; all resolved.

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

These three events all surfaced inside C2 (artifact authoring +
first deployment attempt). Each contributes to a C6 closeout
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
