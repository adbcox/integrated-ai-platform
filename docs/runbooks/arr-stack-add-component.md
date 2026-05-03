# Runbook: Add new arr-stack component

Generalized procedure for adding a new component to the arr-stack
(Lidarr, Autobrr, Profilarr, etc.). Abstracted from the worked
examples Buildarr (D-17-44), Bazarr (D-17-47), Cleanuparr
(D-17-49), and Scraparr (D-17-46). Use this when expanding the
arr-stack ecosystem; for non-arr-stack services, use
`add-new-service.md`.

## Cross-references (do not duplicate here)

- `docs/architecture-facts/vault-agent-sidecar-pattern.md` —
  five-artifact Vault Agent sidecar shape, AppRole bootstrap,
  credential verification (redactor-grep)
- `docs/runbooks/add-new-service.md` — the generic add-new-
  service runbook this builds on
- `docs/architecture-facts/integration-audit-doctrine.md`
  Finding 11 — Buildarr config-as-code doctrine + plugin
  coverage gaps (Sonarr v4, Sportarr)
- `docs/architecture-facts/opnsense-dns-authority.md` — Dnsmasq
  is sole DNS authority for `*.internal`

---

## 1. Pre-flight checks

### 1.1 Image availability

Verify the container image exists and select a pinned tag (or
tag+digest). LinuxServer.io images (`lscr.io/linuxserver/<service>`)
are the platform default for arr-stack. Pull from the deploy host
and confirm before any compose work.

If the upstream image is unavailable or unmaintained (the D-17-49
Huntarr case), preserve the scaffolding under
`docker/_deferred/<service>-upstream-unreachable-<date>/` and
surface back rather than substituting an unverified image.

### 1.2 Buildarr plugin coverage

For Radarr-family services with Buildarr plugin support, declarative
config is canonical. Check coverage by running against a live
instance:

```bash
buildarr <plugin> dump-config
```

Plugin name resolves → declarative management. Plugin name fails
→ reactive/manual management; add to the Buildarr "out of scope"
list per `integration-audit-doctrine.md` Finding 11.

Current gaps as of 2026-05-03: Sonarr v4.0.17, Sportarr, Bazarr,
Cleanuparr, Scraparr, and most non-Radarr-family services.

### 1.3 Scraparr metrics coverage

Scraparr's exporter currently covers Sonarr, Radarr, Prowlarr.
Other arr-stack services need separate exporter or are out-of-
scope for §18.G observability until the exporter expands.

### 1.4 Credential surface

Decide whether the service consumes upstream API keys at runtime.
If yes → Vault Agent sidecar (see cross-reference). If no
(frontend-only or self-generating credentials), no sidecar
required.

For services that generate their own API key in
`/config/config.xml`, the live service is canonical for the
credential, not Vault. Direction is service → Vault, never
reverse (D-17-38 credential-source authority rule).

### 1.5 Network namespace

arr-stack components join the `arr-stack` Docker network so they
can reach each other via container DNS (`http://sonarr:8989`,
`http://radarr:7878`, etc.). This is distinct from the Caddy
reverse_proxy form below.

---

## 2. Compose entry

```yaml
services:
  <service>:
    image: lscr.io/linuxserver/<service>:<pinned-tag>
    container_name: <service>
    restart: unless-stopped
    networks: [arr-stack]
    ports:
      - "<port>:<port>"     # only if direct LAN access needed
    volumes:
      - ~/arr-stack/<service>/config:/config
      - <service>-secrets:/vault/secrets:ro
    depends_on:
      vault-agent-<service>:
        condition: service_completed_successfully
    healthcheck:
      test: ["CMD", "curl", "-fsS", "http://localhost:<port>/ping"]
      interval: 30s
      timeout: 5s
      retries: 3
    cap_drop: [ALL]
    security_opt: [no-new-privileges:true]
```

Two URL forms apply on this platform — do not conflate them:
- **Container-to-container** (e.g. Bazarr → Sonarr): use Docker
  DNS `http://<container>:<port>`. This is the canonical form
  for inter-arr-stack communication.
- **Caddy → arr-stack** (host network bridge): use
  `host.docker.internal:<host_port>` because Caddy is in its
  own container, reaching back to host-published ports. See §3.

Host port mapping (`ports:`) is required only when the service
needs direct LAN access. For Caddy-fronted services that don't
need bypass, container-only is sufficient.

---

## 3. Caddy route

Add to the Media Layer section of `docker/caddy/Caddyfile`,
matching the arr-stack convention:

```
<service>.internal {
    import access_log

    reverse_proxy host.docker.internal:<host_port>
}
```

`host.docker.internal:<host_port>` is correct here; the host_port
must match the compose `ports:` mapping. If the service has no
host port, route through the container DNS form on the
`arr-stack` network instead — but the existing arr-stack pattern
publishes host ports, so prefer the standard form unless there's
a reason to deviate.

The `access_log` snippet routes to the per-site Loki pipeline
(D-LOG, Phase 14) — do not author a fresh log directive.

---

## 4. Dnsmasq override

Add a `*.internal` host record so LAN clients can resolve. Per
`opnsense-dns-authority.md` (D-17-21), Dnsmasq on OPNsense is
the sole authority for `*.internal`; Unbound is forbidden.

For Caddy-fronted services the IP is **always** Mac Mini
(192.168.10.145), not the upstream container's IP — Caddy is
the entrypoint.

OPNsense GUI: `Services → Dnsmasq DNS → Hosts → +` with
`host=<service>`, `domain=internal`, `IP=192.168.10.145`. Then
run `scripts/check-repo-coherence.py caddy-dns-parity` and verify
exit 0; the parity check is enforced pre-commit.

> **Note:** `docs/runbooks/opnsense-add-host-overrides.md` is
> stale (refers to Unbound, which is disabled per D-17-21).
> Backlog candidate to update or supersede; until then, follow
> the Dnsmasq path above.

---

## 5. Vault Agent sidecar (cross-reference only)

Follow `vault-agent-sidecar-pattern.md` for the full five-artifact
shape. The arr-stack particulars:

- **AppRole name:** `<service>` (no prefix)
- **Vault path:** `secret/data/arr/<service>` (KV v2, the `data`
  segment is part of the path)
- **Template variable:** `<SERVICE>_API_KEY` (uppercase service
  name + `_API_KEY` suffix)
- **Sidecar container:** `vault-agent-<service>`
- **Provision script:** `scripts/provision-<service>.sh`
- **Policy file:** `config/vault-policies/<service>-policy.hcl`

Run the provision script once on the deploy host, then bring up
the compose entry. Verify credential delivery using the
redactor-grep pattern from the sidecar-pattern chronicle —
**do not author a fresh `/proc/1/environ` grep here**, the
canonical form is in the sidecar-pattern chronicle and a
duplicate would drift.

---

## 6. Buildarr declarative config (if covered)

If §1.2 returned a supported plugin, add a stanza to
`config/arr-stack/buildarr/buildarr.yml`. The Vault Agent sidecar
substitutes `${<SERVICE>_API_KEY}` at runtime via
`scripts/buildarr-run.sh`.

Scheduled run is daily at 03:00 (launchd
`com.iap.buildarr-sync`). Manual run: `scripts/buildarr-run.sh`.
Syntax-check only: `scripts/buildarr-run.sh --check`.

If the plugin is missing, document the reactive-management
posture and add the service to the Buildarr "out of scope" list
per `integration-audit-doctrine.md` Finding 11. Do not pretend
declarative coverage exists.

---

## 7. Initial deployment + smoke test

```bash
# Provision Vault AppRole + policy (once per host)
scripts/provision-<service>.sh

# Bring up the new service
docker compose -f docker/compose.yml up -d vault-agent-<service> <service>

# Verify container health
docker compose ps <service>      # expect "healthy"

# Verify direct port (host-side test)
curl -fsS http://localhost:<host_port>/ping

# Verify Caddy route (host-side test, internal TLS)
curl -k --resolve <service>.internal:443:127.0.0.1 \
  https://<service>.internal/ping

# Verify credential delivery (redactor-grep, presence-only)
docker exec <service> sh -c 'tr "\0" "\n" < /proc/1/environ' \
  | grep ^<SERVICE>_API_KEY= \
  | sed 's/=.*/=<set>/'
```

If the service is consumer-side (e.g. Bazarr → Sonarr/Radarr),
the integration smoke also includes a container-DNS reachability
test from inside the consumer:

```bash
docker exec <service> sh -c 'curl -fsS http://sonarr:8989/api/v3/system/status' \
  > /dev/null && echo "sonarr reachable from <service>"
```

LAN DNS resolution (post-Dnsmasq override) takes a few minutes to
propagate; if `<service>.internal` doesn't resolve immediately,
flush the resolver and retry.

---

## 8. Doctrine integration

After the deployment is healthy:

1. **Service registry refresh.** `scripts/platform-registry/refresh.sh`
   to update `~/.platform-registry/inventory.json` (D-17-29).
2. **Framework row.** If this addition is its own deliverable
   (D-NN-MM), add a row to `PROJECT_FRAMEWORK.md` §9 with status
   IN PROGRESS / DONE per close state.
3. **Chronicle entry.** If the addition surfaces a new finding
   (failure mode, doctrine refinement), append to
   `integration-audit-doctrine.md` with the next Finding number.
4. **OpenProject sync.** Run
   `python3 scripts/openproject-sync-from-framework.py` —
   the new framework row propagates automatically.
5. **Buildarr drift check.** If §6 added a Buildarr stanza, run
   `buildarr <plugin> dump-config` and diff against the
   committed YAML to confirm no drift.
6. **DNS parity check.** `scripts/check-repo-coherence.py
   caddy-dns-parity` to confirm the Caddy site and Dnsmasq
   record agree.

---

## When NOT to use this runbook

- **Non-arr-stack services** — use `add-new-service.md`.
- **Frontend-only additions** that don't consume upstream APIs
  — Vault Agent sidecar is unnecessary; trim §5.
- **Replacing an existing arr-stack service** — different shape
  (rotation + drain), not addition. Author a per-deliverable
  runbook.
