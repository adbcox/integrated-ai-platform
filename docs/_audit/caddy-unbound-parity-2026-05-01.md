# Caddy ↔ Unbound DNS Parity — Initial Reconciliation

**Date:** 2026-05-01
**Deliverable:** 17.I (initial run after the parity check became enforced)
**Source command:** `scripts/check-repo-coherence.py caddy-unbound-parity --refresh`
**Status file:** `~/.platform-logs/caddy-unbound-parity.json`

---

## Surface

| Metric | Value |
|---|---|
| Caddy `*.internal` site blocks | 31 |
| Unbound enabled `.internal` A-records | 38 |
| **Missing** (Caddy site without Unbound override) | **8** |
| **Wrong target** (Unbound override pointing somewhere other than 192.168.10.145) | **0** |
| **Extra** (Unbound override with no Caddy site — informational) | 15 |

The check is now enforcing. Until the 8 gaps are closed, the operator-Mac
`scripts/check-repo-coherence.py all` exits 1; CI/pre-commit are unaffected
because the status-file pattern `SKIP`s when no status file is present
(see `docs/runbooks/drift-detection.md` §9).

---

## Operator action items — add 8 missing Unbound A-records

Each entry below needs an Unbound override added in OPNsense:

> **OPNsense UI path:** Services → Unbound DNS → Overrides → Host Overrides → +
>   - Host: *(left column below)*
>   - Domain: `internal`
>   - Type: `A`
>   - IP: `192.168.10.145`
>   - Description: e.g. `iap-platform — Caddy-fronted`

| Hostname | FQDN | Notes |
|---|---|---|
| docs | `docs.internal` | Docs site (in Caddyfile; verify which container) |
| homeassistant | `homeassistant.internal` | Home Assistant Caddy front |
| inventree | `inventree.internal` | InvenTree Caddy front (Phase 13 inventory CMDB-adjacent) |
| loki | `loki.internal` | Loki UI exposed via Caddy (Phase 14 D-LOG) |
| mcp-xindex | `mcp-xindex.internal` | xindex MCP wrapper (Phase 17 D-16-02.3) |
| netbox | `netbox.internal` | NetBox CMDB (authoritative source per Phase 14 D-DOC) |
| structurizr | `structurizr.internal` | Structurizr architecture diagrams |
| xindex | `xindex.internal` | xindex cross-index UI (Phase 17 17.S/17.T) |

**Priority:** netbox.internal and the two xindex domains are load-bearing
for the cross-index/CMDB workflow — operator should add those first.
Loki and structurizr are observability/docs surfaces with lower
disruption risk if currently unreachable by hostname.

After each batch, run:

```bash
scripts/check-repo-coherence.py caddy-unbound-parity --refresh
```

`missing` should drop. When `missing == 0 && wrong_target == 0`, the
status file flips `ok=true` and the read-mode check passes.

---

## Informational — 15 Unbound `.internal` records with no Caddy site

These are operator-owned infrastructure A-records that don't have a
Caddy reverse proxy in front of them. Not drift; documented for
awareness only.

| FQDN | Likely role | Action |
|---|---|---|
| `bookstack.internal` | docs/wiki | none — direct port access |
| `dashboard.internal` | (legacy?) | candidate for retirement check (was pruned from Caddy in commit 3db56c7) |
| `dozzle.internal` | docker log viewer | none — direct port access |
| `filebrowser.internal` | filebrowser UI | none — direct port access |
| `gitea.internal` | self-hosted git | none — direct port access |
| `mac-mini.internal` | the host itself | KEEP — used by `extra_hosts` in many compose files |
| `manyfold.internal` | 3D model library | none — direct port access |
| `n8n.internal` | workflow automation | none — direct port access |
| `netdata.internal` | host metrics UI | none — direct port access |
| `overseerr.internal` | media request UI | none — direct port access |
| `pgadmin.internal` | postgres admin UI | none — direct port access |
| `portainer.internal` | docker UI | none — direct port access |
| `qnap.internal` | NAS host | KEEP — used by `extra_hosts` |
| `ragflow.internal` | RAG service | none — direct port access (consider Caddy front when surfaced) |
| `tautulli.internal` | Plex stats | none — direct port access |

**`dashboard.internal`** is a low-grade follow-up: it was pruned from
Caddy in commit `3db56c7` (Phase 13 Block 2 follow-up #1). The Unbound
record could be removed at the same operator session that adds the 8
missing entries above. Not blocking.

---

## What changes after these records are added

1. The next nightly `com.iap.caddy-unbound-parity` launchd refresh
   (04:23 daily) will write `ok: true` to the status file.
2. Pre-commit local hook `caddy-unbound-parity` will pass on the next
   Caddyfile-touching commit.
3. The CI job `validate-caddy-dns-parity` continues to `SKIP` (no
   status file in CI runner — that's correct status-file pattern
   behavior).
4. Adding a NEW `*.internal` site to the Caddyfile WITHOUT an
   accompanying Unbound override will now fail the local pre-commit
   hook, surfacing the gap immediately.

---

## Related artifacts

- `scripts/opnsense_client.py` — OPNsense API client (17.I T2)
- `scripts/check-repo-coherence.py` `caddy-unbound-parity` subcommand (17.I T3)
- `docker/launchd-agents/com.iap.caddy-unbound-parity.plist` — daily refresh job (T3.1)
- `config/vault-policies/opnsense-api-reader-policy.hcl` — least-privilege Vault policy (T1)
- `docs/runbooks/drift-detection.md` §9 — operator doctrine for this check (T5)
- D-16-06 — original drift-detection deliverable that flagged this gap as advisory
- 17.I — this deliverable (closes the advisory→enforced gap)
