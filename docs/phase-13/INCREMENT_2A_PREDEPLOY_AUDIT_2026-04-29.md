# Phase 13 Increment 2A — 4.D.1 pre-deploy audit

**Date:** 2026-04-29
**Sub-phase:** 4.D.1 (Pre-deploy preparation)
**Gate type:** Full IV&V (per Appendix D §Increment 2)
**Status:** Audit complete; awaiting operator gate review before 4.D.2 deploy.

This document is the load-bearing artifact for the 4.D.1 → 4.D.2 gate.
Operator confirms the audit findings before any container is brought up.

---

## 1. Surface inventory

What was read for this audit:

| Source | Purpose |
|---|---|
| `docker/netbox/docker-compose.yml` | Canonical Vault Agent sidecar pattern reference. |
| `docker/netbox/README.md` | Bootstrap procedure and hash-only verification template. |
| `docker/netbox/vault-agent-netbox/{agent.hcl,credentials.env.tmpl}` | Sidecar config shape (replicated). |
| `scripts/provision-netbox.sh` | Vault provisioning helper template (replicated). |
| `config/vault-policies/netbox-policy.hcl` | Policy shape (replicated for inventree). |
| `docker/caddy/Caddyfile` | Auto-TLS routing pattern for `*.internal` hosts. |
| `docs/inventree.org/en/stable/start/config/` (upstream docs) | Verbatim env-var names. |
| `docs.inventree.org/en/latest/start/docker/` | Container topology (server, worker, db, cache). |
| `docs.inventree.org/en/latest/plugins/install/` | Plugin install mechanism (plugins.txt + invoke). |
| Docker Hub `inventree/inventree` tags | Image pinning (latest stable concrete tag = 1.0.9). |

## 2. Findings by item

### 2.1 Port-conflict pre-check

Ran `lsof -nP -iTCP -sTCP:LISTEN` on Mac Mini against the candidate
port range 8000–8090. Cross-referenced with `docker ps` published-
port output.

| Port | Status | Holder |
|---|---|---|
| 8000 | **CONFLICT** | `docker-plane-api-1` publishes 8000 → 8000 |
| 8001 | free | — |
| 8080 | in use | Python listener (cAdvisor inside container, but its host-side publish is 8088) — also a ssh-tunnel artifact; safe but ambiguous |
| 8084 | in use | `netbox` (127.0.0.1:8084 → 8080) |
| 8085 | in use | `nextcloud` |
| 8086 | in use | `control-plane` |
| **8087** | **free** | ← chosen for InvenTree |
| 8088 | in use | `cadvisor` |
| 8089 | free | — |
| 8090 | in use | `obot` |

**Decision:** Bind host `127.0.0.1:8087` → container port `8000`
(InvenTree's gunicorn listens on 8000 internally per upstream).
Loopback-only published port mirrors NetBox's `127.0.0.1:8084`
pattern; external access flows through Caddy with TLS termination
at the reverse proxy.

**Pattern continuity:** Block 4.C C2 Discovery #1 documented the
8080-busy-with-dashboard pivot to 8084. This audit applies the same
pattern: pick the next free loopback port outside the
SSH-tunnel-reserved range, re-export through Caddy.

### 2.2 Vault path provisioning

Provisioning script: `scripts/provision-inventree.sh` (idempotent;
hash-only verification; per-key rotation gates).

Vault paths created (hash-only verification at deploy time, not
displayed during audit):

| Path | Field | Generator | Purpose |
|---|---|---|---|
| `secret/inventree/postgres` | `password` | `openssl rand -hex 32` | Postgres user password |
| `secret/inventree/redis` | `password` | `openssl rand -hex 24` | Redis cache password |
| `secret/inventree/secret_key` | `value` | `openssl rand -hex 32` | Django SECRET_KEY |
| `secret/inventree/admin` | `password` | `openssl rand -hex 24` | Admin bootstrap password |
| `secret/inventree/admin` | `username` | literal `admin` | Admin username |
| `secret/inventree/admin` | `email` | literal `admin@inventree.internal` | Admin email |
| `secret/inventree/api_token` | `token` | empty placeholder | Populated post-deploy in 4.D.2 |

Generator rationale: 32-byte hex matches NetBox's choice for the
postgres password and the Django SECRET_KEY (Django requires ≥50
chars; 64 hex chars = 32 bytes satisfies). 24-byte hex = 48 hex chars
for non-Django passwords matches NetBox's convention.

### 2.3 Vault policy

`config/vault-policies/inventree-policy.hcl` — drafted, mirrors
`netbox-policy.hcl` shape.

Policy posture:
- Read-only on all `secret/data/inventree/*` paths consumed by the
  three sidecars + future supplier-panel plugin.
- `list` + `read` on `secret/metadata/inventree/*` for hash-only
  verification tooling.
- `read` on `sys/health` and `sys/seal-status` (status checks).
- **Explicit deny** on `sys/policies/acl/*` and
  `auth/approle/role/*` (belt-and-suspenders against
  privilege escalation; matches netbox-policy precedent).

Supplier paths (`secret/data/mouser`, `secret/data/digikey`) are
**not** in the policy yet. They land in Increment 2B when those
Vault paths exist; adding them now would attach reads against
non-existent paths (no-op, harmless, but doctrine prefers
incremental policy alignment with deployed surface).

### 2.4 AppRole

Single AppRole `inventree` with policy `inventree`. Same shape as
NetBox's AppRole:

```
token_policies = inventree
token_ttl      = 1h
token_max_ttl  = 4h
secret_id_ttl  = 0    # role-managed, not rotated by Vault
```

`role-id` and `secret-id` written under
`/Users/admin/.vault-approle/inventree/` with mode 0600. The three
Vault Agent sidecars (inventree app/worker, inventree-postgres,
inventree-redis) all bind-mount this directory read-only and use
the same AppRole — exactly the netbox precedent.

### 2.5 Compose authoring

`docker/inventree/docker-compose.yml` — drafted.

Container roster (6 containers total, 3 Vault Agent sidecars + 3
service containers):

| Container | Image | Purpose | Mem | Pub-port |
|---|---|---|---|---|
| `vault-agent-inventree` | `hashicorp/vault:2.0.0` | Renders `credentials.env` for app+worker | default | — |
| `vault-agent-inventree-postgres` | `hashicorp/vault:2.0.0` | Renders `POSTGRES_PASSWORD` | default | — |
| `vault-agent-inventree-redis` | `hashicorp/vault:2.0.0` | Renders `REDIS_PASSWORD` | default | — |
| `inventree-postgres` | `postgres:17-alpine` | Postgres database | 1g | — |
| `inventree-redis` | `redis:7-alpine` | Redis cache | 256m | — |
| `inventree` | `inventree/inventree:1.0.9` | Django + gunicorn server | 2g | 127.0.0.1:8087→8000 |
| `inventree-worker` | `inventree/inventree:1.0.9` | django-q background worker | 1g | — |

7 service containers (counting the worker as a separate row).

Image pinning rationale:
- **inventree/inventree:1.0.9** — latest pinned stable on Docker Hub
  (verified by Docker Hub tag listing). The `stable` floating tag
  resolves to this same release. Pinned to the concrete tag for
  reproducibility; upgrades follow the explicit-pin-bump pattern
  documented in `docker/netbox/README.md` §Upgrades.
- **postgres:17-alpine** — matches NetBox's pin (Block 4.C C2
  Discovery captured the pg18 → pg17 pivot; stay on pg17 until
  upstream evidence supports pg18).
- **redis:7-alpine** — InvenTree's docs use Redis (not Valkey) for
  its optional cache. Stay upstream-faithful.

Hardening posture (matches NetBox):
- `cap_drop: [ALL]` universally; minimal `cap_add` per workload.
- `security_opt: [no-new-privileges:true]` universally.
- `mem_limit` calibrated against postgres `shared_buffers` headroom;
  no `read_only: true` (Django collects static, postgres writes,
  Redis AOF — none are read-only-friendly).

PID-1 doctrine: every service container's `entrypoint` or `command`
ends in `exec <real-binary>` after sourcing `credentials.env`.
Healthchecks source `credentials.env` themselves rather than
inherit PID-1 env (canonical lesson from Block 4.C).

### 2.6 Caddy route

Added block in `docker/caddy/Caddyfile`:

```
inventree.internal {
    import access_log

    reverse_proxy host.docker.internal:8087
}
```

Uses the standard `(access_log)` snippet (rolled JSON access log,
100 MiB rotation, 7 keeps — same as every other `*.internal`
service). Caddy's automatic-TLS-for-`.internal` covers the cert
issuance via the platform's local CA root.

### 2.7 Plugin posture for 2A

Plugins **enabled** but **none installed** in 2A:

- `INVENTREE_PLUGINS_ENABLED=true` — verbatim env-var name from
  upstream docs; activates the plugin subsystem.
- `INVENTREE_PLUGIN_NOINSTALL=false` — allows the server to
  process `plugins.txt` on startup. Set to `true` for production-
  immutable deployments where plugins must be baked in at image
  time; we use `false` so 2B can drop a plugin into `plugins.txt`
  and restart the server to pick it up.
- `INVENTREE_PLUGIN_FILE=/home/inventree/data/plugins.txt` —
  explicit path on the persistent data volume. Empty in 2A; 2B
  appends `inventree-supplier-panel` and `inventree-part-import`.

Plugin sandboxing/signature: upstream docs do **not** document
sandboxing or signature verification for InvenTree plugins. This
is acceptable for the platform's threat model (plugins installed
by the operator, not by untrusted users) but worth flagging as a
known posture (see §3 below).

## 3. Risks the audit cannot resolve

| Risk | Why audit can't resolve | Resolution path |
|---|---|---|
| First-boot migration time | InvenTree on first boot runs Django migrations against an empty DB; duration unknown for this stack until measured. | 4.D.2 startup measurement; healthcheck `start_period: 120s` is a generous estimate but may need extension. |
| Plugin install behaviour | The `INVENTREE_PLUGIN_NOINSTALL=false` + plugins.txt mechanism is documented but unverified on this image revision. | 4.D.2 plugin install step is the validation. |
| Worker → app coordination | django-q worker needs DB + cache; the `depends_on inventree:service_healthy` may be too strict if the app's healthcheck is lazy. | 4.D.2 deploy logs — fall back to `inventree-postgres:service_healthy` + `inventree-redis:service_healthy` if the app dependency creates a startup loop. |
| InvenTree user UID/GID | Upstream image documents a `inventree:inventree` user; the bind-mounted Vault secrets dir owner mismatch could block reads. | 4.D.2 `docker logs vault-agent-inventree` will surface; mitigation is the existing pattern (the agent writes to a Docker-managed bind mount, host UID is irrelevant). |
| Plugin sandbox absence | InvenTree plugins run in-process with full Django access. | Acceptable for trusted-operator install; documented as known posture. No remediation in 2A. |

## 4. Scope ratification

The 4.D.1 sub-phase work is bounded as follows. **No work outside
this list happens before the operator gate.**

- ✅ Port-conflict scan (done; 8087 chosen)
- ✅ Vault policy authored (`config/vault-policies/inventree-policy.hcl`)
- ✅ Vault Agent sidecar configs authored (3 sidecars × 2 files)
- ✅ Compose file authored (`docker/inventree/docker-compose.yml`)
- ✅ Provisioning script authored (`scripts/provision-inventree.sh`)
- ✅ Caddy route authored (`docker/caddy/Caddyfile` block added)
- ✅ Audit document (this file)

**Deferred to 4.D.2 (next sub-phase, post-gate):**
- Run the provisioning script against Vault (creates AppRole + populates secrets)
- `docker compose up -d` (brings the stack online)
- Bootstrap admin (handled by InvenTree's first-boot flow via env vars)
- Reload Caddy to apply the new `inventree.internal` route
- Plugin installation validation

**Out of scope for Increment 2A entirely (deferred to 2B):**
- Mouser API credential provisioning + integration
- DigiKey OAuth flow + integration
- 129-component CSV import
- NetBox cross-reference custom field
- Supplier-panel plugin configuration

## 5. Operator gate

Before 4.D.2 begins, operator confirms:

1. **Port choice:** 8087 acceptable, or specify alternative.
2. **Image pin:** `inventree/inventree:1.0.9` acceptable, or specify
   alternative.
3. **Plugin posture:** plugins enabled, two plugins to-be-installed
   (`inventree-supplier-panel`, `inventree-part-import`),
   no sandbox — acceptable.
4. **Compose review:** `docker/inventree/docker-compose.yml` reviewed
   by operator (or operator delegates to `claude-pro` review).
5. **Provisioning script:** operator runs
   `sudo -E ./scripts/provision-inventree.sh` after gate, OR
   operator authorises the executing session to run it.

If all five clear: gate passes, advance to 4.D.2.

## 6. Cross-references

- **Plan source:** `docs/phase-13/PHASE_13_CLOSEOUT_CAMPAIGN_PLAN_2026-04-29.md`
  Appendix D §Increment 2 (4.D.1 entry).
- **Doctrine:** A-011 (IV&V loop pattern for the audit/exec/validation/regression
  shape of this sub-phase).
- **Pattern source:** `docker/netbox/` (Block 4.C C2 — canonical Vault
  Agent sidecar deployment).
- **2A scope split:** Increment 2A execution prompt (operator-issued
  2026-04-29) explicitly excluded 4.D.3–4.D.6 pending external
  prerequisites (Mouser key, DigiKey OAuth, components CSV).
