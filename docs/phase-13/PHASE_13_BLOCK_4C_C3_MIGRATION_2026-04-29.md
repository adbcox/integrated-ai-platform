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

## C3.4 — Live migration (pending approval)

(To be filled in after gate approval.)
