# Phase 13 — Block 4.C — C3 Registry → NetBox migration

**Date:** 2026-04-29
**Phase:** Block 4.C, Phase C3 (Registry → NetBox data migration)
**Status:** C3.1 ✅ custom fields/tags provisioned · C3.2 ✅ scripts written · C3.3 ⏸ dry-run complete, awaiting operator approval before C3.4 live

---

## C3.1 — Custom fields + tags provisioned

Provisioned via `scripts/netbox-custom-fields.py` (idempotent).

**14 custom fields on `ipam.service`:**

| Name | Type | Notes |
|---|---|---|
| `registry_id` | text | canonical key from registry |
| `container_name` | text | from `container` |
| `container_image` | text | from `image` |
| `health_url` | text | |
| `health_method` | text | |
| `health_expect` | integer | list values like `[200, 302]` collapsed to first; defaults 0 if missing |
| `compose_file` | text | |
| `vault_paths` | longtext | `credentials_env` + normalized `credentials` joined with newlines |
| `security_profile` | longtext | JSON-as-string of nested `security` block |
| `public_values` | longtext | JSON-as-string of `public_values` |
| `service_notes` | longtext | from `notes` (`description`/`comments` carry `name` + `purpose`) |
| `sidecar_of` | text | |
| `superseded_by` | text | |
| `service_dependencies` | multi-object → `ipam.service` | per C1 Decision 2 — native graph traversal |

**19 tags:**
- 16 categories: `ai`, `automation`, `cmdb`, `control-center`, `data`, `home-automation`, `infrastructure`, `integration`, `mcp`, `mcp-shim`, `media`, `monitoring`, `network`, `observability`, `platform`, `visibility`
- 2 kinds: `sidecar`, `support-service`
- 1 lifecycle: `deprecated`

---

## C3.2 — Migration script

`scripts/migrate-registry-to-netbox.py`:
- Reads `config/service-registry.yaml`.
- De-duplicates by `id` (last-wins, with NOTE log per dup) — resolves C1 audit Finding A.
- Two-pass: services first, then `depends_on` resolved via the multi-object custom field.
- `--dry-run` mode prints planned actions without API writes.
- Token sourced from `/Users/admin/.vault-agent-secrets/netbox/credentials.env` `NETBOX_API_TOKEN` (full V2 wire form).
- Idempotent: every upsert is keyed by stable name; re-runs yield "skip" actions.

### NetBox object shapes

| Source | NetBox target |
|---|---|
| 4 hosts | `dcim.site` (1) + `dcim.device` (4, one per host) anchored on stub manufacturer/device-type/role named `platform-host` |
| 75 services | `ipam.service` attached to host's device; ports from `port` (fallback `internal_port`); tags from `category`/`kind`/`deprecated`; metadata in custom fields |

Note: registry counts 76 entries; after de-dup = 75 (uptime-kuma collapse).

---

## C3.3 — Dry-run output (operator review)

### Discovery #8 — V2 wire token assembly required

NetBox 4.5 introduced **V2 tokens** (`nbt_<key>.<secret>`); pynetbox 7.6+ auto-detects the `nbt_` prefix and uses `Authorization: Bearer ...`. C2 stored only the secret half (40 hex chars) in Vault; the public 12-char `key` part lived in the DB only.

**Resolution applied at C3:**
1. Extracted `key` from the live Token via Django shell (one-time bootstrap).
2. Wrote it under `secret/netbox/api_token#key` (idempotent).
3. Updated `vault-agent-netbox/credentials.env.tmpl` to render an additional `NETBOX_API_TOKEN=nbt_<key>.<secret>` line for API consumers.
4. Migration script reads `NETBOX_API_TOKEN`; falls back with a clear error.

**Canonical-pattern note for C6:** "V2 token bootstrap requires a one-time DB→Vault key extraction; subsequent renders are pure-Vault."

### Discovery #9 — Registry de-dup needed (C1 Finding A confirmed live)

`uptime-kuma` is defined twice in `service-registry.yaml`:
- Line 315: `category: observability`, `health_expect: [200, 302]`
- Line 1145: `category: visibility`, `health_expect: 200`

**Script behavior:** dedup by id, last-wins → uses the line-1145 entry (visibility / 200). NOTE logged. Per C1 audit's "option 1" recommendation, in-script dedup with log.

**For C5/C6:** the duplicate entry should be deleted from `service-registry.yaml` before C5 deprecates the registry, so we don't silently inherit ambiguity.

### Discovery #10 — Stale `depends_on` references in registry

8 dependency warnings:
- 6 services depend on `vault-server` (the actual registry id is `vault`): `homepage`, `control-plane`, `plex-mcp`, `netbox`, `netbox-postgres`, `netbox-redis`, `netbox-redis-cache`.
- 2 services depend on `grafana-obs` (the actual registry id is `grafana`): `homepage`, `topology-api`.

These are pre-existing registry hygiene bugs not introduced by this migration. The script logs them as `warn` and the dependency edges are dropped (current `validate-cmdb.sh` and topology-api also drop unresolved edges silently per its `notes`).

**Resolution choice surfaced for operator:**
- **Option A:** fix the registry now (rename `vault-server`→`vault`, `grafana-obs`→`grafana`) before C3.4 live migration. ~10 minutes.
- **Option B:** proceed with C3.4 as-is; capture as a C5 follow-up (registry-deprecation phase will rewrite consumers anyway). The 8 missing edges show as `warn` lines on every run.
- **Option C:** add the missing services (`vault-server`, `grafana-obs`) to the registry. *Not recommended* — `vault` is the right id for the Vault service.

Recommendation: **Option A** — these are 1-line fixes and the migration's dependency graph is the marquee artifact of C3. Better to land it clean.

### Summary table

| Verb | Type | Count |
|---|---|---|
| create | site | 1 |
| create | manufacturer | 1 |
| create | device_type | 1 |
| create | device_role | 1 |
| create | device | 4 |
| create | service | 75 |
| update | deps | 42 |
| warn | deps | 8 |

**Total writes planned:** 83 creates + 42 dep-updates = **125 API operations** in live mode.

---

## 🛑 GATE C3 — User approval required before C3.4

### Operator decision points

1. **Approve dependency-warning resolution:** A / B / C above (recommend A).
2. **Approve dry-run plan as-is:** 75 services / 4 devices / 1 site / 42 dep updates / 8 warns.
3. **Approve progression to live (`--apply` / no flag):** the script is fully idempotent so re-runs after partial failure are safe.

### What live execution will produce

- Each registry entry creates one `ipam.service` named after its `id`.
- Tags applied: category + (sidecar | support-service when present) + (deprecated when set).
- Custom fields populated; `service_dependencies` resolved to actual NetBox object IDs.
- A side-by-side validation report (next addition to this file under "C3.4") will compare each registry entry's normalized field values to the NetBox-loaded view and surface mismatches.

### What live will NOT do

- Deprecate or remove `service-registry.yaml` (C5 territory).
- Touch any consumer (`scripts/validate-cmdb.sh`, `scripts/topology-api.py`, etc.) — those keep reading the YAML until C5 migrates them.
- Generate any plain-text token output. All token reads stay hash-only or via Vault Agent.

---

## C3.4 — Live migration (executed 2026-04-29)

### Discovery #10 resolution

Per operator decision Option A: registry corrected at source before live migration.
- Commit `dc9b7ac` — "Block 4.C registry hygiene: fix 8 stale depends_on refs (Discovery #10)"
- 6 services: `vault-server` → `vault` (homepage, control-plane, plex-mcp, netbox, netbox-postgres, netbox-redis, netbox-redis-cache)
- 2 services: `grafana-obs` → `grafana` (homepage, topology-api)

Re-run dry-run after the fix: **0 dep warnings**, 47 dep updates planned.

### Discovery #11 — `ipam.service` generic FK shape (NetBox 4.5)

NetBox 4.5 changed `ipam.service`'s parent reference from a direct `device` FK to a generic `parent_object_type` + `parent_object_id` pair. The first live attempt failed with `400: parent_object_type / parent_object_id required`. Site + 4 devices were created cleanly (legacy shape valid for `dcim`); services failed before any was created.

**Resolution** (commit `6ae8699`): switched payload to `parent_object_type="dcim.device"` + `parent_object_id=<device_id>`.

### Discovery #12 — Sentinel port for port-less services

Some registry entries are workers / housekeeping pods with no host-port binding (`port: null`). NetBox `ipam.service.ports` requires non-empty. Second live attempt failed at `netbox-housekeeping` with `400: ports may not be empty`.

**Resolution** (commit `846c81b`): use sentinel port `1` (TCP `tcpmux`, RFC1340) for port-less services. Port 1 cannot collide with a real binding. **2 services** in the live set carry the sentinel: `netbox-worker`, `netbox-housekeeping`. These will be filtered in any "what's actually listening" query by `port != 1`.

### Discovery #9 reminder — `uptime-kuma` de-dup behavior

Per operator-approved C1 audit Option 1: **last-wins with NOTE log**. The NetBox object reflects the *line-1145* entry (`category: visibility`, `health_expect: 200`). The line-315 entry (`category: observability`, `health_expect: [200, 302]`) is silently ignored at load time. **Action item for C5 / registry cleanup:** delete the duplicate line-315 entry before C5 deprecates the YAML.

### Live migration result

```
── Summary ────────────────────────────────────────────────
  create   service            5
  skip     device_role        1
  skip     manufacturer       1
  update   deps               47
  update   device             4
  update   device_type        1
  update   service            70
  update   site               1
```

(`update service: 70` are services created during the post-#11 attempt 2 partial; `create service: 5` are the post-housekeeping tail. Total = 75 services in NetBox.)

### Validation report

```
NetBox state after C3.4:
  sites:        1
  devices:      4    (mac-mini=72 svcs, opnsense=1, ha-device=1, qnap=1)
  services:    75
  tags:        19
  custom-fields:14
  total dep edges: 72   (47 source-services × varying depth, see below)

Sample object (litellm-gateway):
  name:               litellm-gateway
  description:        LiteLLM Gateway
  ports:              [4000]
  protocol:           TCP
  parent_object_type: dcim.device
  tags:               ['ai']
  cf.registry_id:     litellm-gateway
  cf.container_image: ghcr.io/berriai/litellm:main-latest
  cf.health_url:      http://localhost:4000/health/liveliness
  cf.compose_file:    control-center-stack/stacks/gateways/docker-compose.yml

Side-by-side validation (NetBox vs registry, all 75 services):
  checked: 75
  mismatches: 0
  fields compared: container_image, container_name, health_url, compose_file

Dependency-graph spot check (homepage, the densest node):
  registry depends_on:        8 entries
  NetBox service_dependencies: 8 entries
  resolved names: vault, caddy, sonarr, radarr, prowlarr, grafana,
                  plane-api, uptime-kuma  (all clean post-#10)

Idempotency probe (re-run with no registry changes):
  zero new creates
  zero new dep changes (skip deps: 47)
  cosmetic re-PUTs on services / device / site
    (root cause: payload uses string for protocol/tags ID; pynetbox
     returns Record objects → comparator sees diff. Live data
     unchanged. Minor; not blocking.)
```

### Tag distribution

| Tag | Service count |
|---|---|
| mcp-shim | 17 |
| platform | 14 |
| ai | 9 |
| observability | 6 |
| support-service | 6 |
| data | 5 |
| media | 5 |
| cmdb | 3 |
| mcp | 3 |
| monitoring | 3 |
| automation | 2 |
| control-center | 2 |
| infrastructure | 2 |
| deprecated | 1 |
| home-automation | 1 |
| integration | 1 |
| network | 1 |
| sidecar | 1 |
| visibility | 1 |

### C3 status

✅ All 75 services migrated cleanly · ✅ All 47 dep-source services have their cross-references resolved (72 total dependency edges in the graph) · ✅ Zero side-by-side mismatches · ✅ Sentinel-port services correctly flagged · ✅ Idempotency holds for the dependency graph; cosmetic re-PUTs on services are not data drift.

### C5 / cleanup follow-ups (added to /tmp/c6_followups.txt)

7. Cosmetic-only idempotency: protocol/tag payload comparator should normalize `Record` objects to ID/value before diffing (live data unchanged; PUTs are no-ops; nice-to-have not need-to-have).
8. Registry cleanup before C5: delete the duplicate `uptime-kuma` entry on line 315 of `service-registry.yaml` (line 1145 is canonical per current dedup behavior).
