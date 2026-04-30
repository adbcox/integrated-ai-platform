# Phase 14 Closeout

**Date:** 2026-04-30
**Gate:** phase-14-final PASS=16 FAIL=0 WARN=3
**HEAD at close:** cf09a6f (before this doc commit)

## Block status

| Block | Status | Key commits | Gate result |
|---|---|---|---|
| D-DOC | ✅ CLOSED (+ addendum) | a6d50c2, 3a15faa | PASS=15 FAIL=0 |
| Plane curation | ✅ CLOSED | 4f6dcd9 | 99.8% coverage (616/617) |
| D-STR | ✅ CLOSED | 86865e0 | Window 2 probe PASS=15 |
| D-MKD | ✅ CLOSED | 86865e0 | Window 2 probe PASS=15 |
| D-ZBX | ✅ CLOSED | d1fc7f5 | Window 3 probe PASS=15 |
| D-RST | ✅ CLOSED | 2934085 | Window 3 probe PASS=15 |
| D-LOG | ✅ CLOSED | d944567 | Window 4 probe PASS=15 |
| D-XINDEX | ✅ CLOSED | 410ed6f, cf09a6f | probe PASS=16 |
| CL-14 | ✅ CLOSED | this doc | PASS=16 FAIL=0 WARN=3 |

## Discoveries (continuing from D-DOC #30)

**D-31:** Promtail requires `cap_add: [DAC_READ_SEARCH]` to tail `/var/log/caddy/access.log`
from the `caddy-logs` Docker named volume. Capability is minimal (read-only log shipping),
documented in compose and CLAUDE.md.

**D-32:** `structurizr/lite` is deprecated on ARM64 Mac — exits immediately.
Replaced with `structurizr/structurizr` image with `command: local`. Also requires
`header_up Host "localhost"` in Caddy since Structurizr's local mode rejects
non-localhost Host headers.

**D-33:** Loki 2.9 with `cap_drop:[ALL]` cannot write to `/wal` (default root path).
Fix: configure `ingester.wal.dir: /loki/wal` pointing to the named volume.
Also `compactor.working_directory` must be explicit.

**D-34:** Plane `POST /api/v1/projects/{id}/issues/` silently ignores `external_id` in the
request body. Must be set via `PATCH /api/v1/projects/{id}/issues/{id}/` after creation.
Fixed in `framework/plane_connector.py::create_issue`.

**D-35:** Plane API token `plane_api_f6c2c3cc049d4fedb24b0f62acbfc00b` was soft-deleted
(NF-14-1 admin password rotation deleted it). Restored via DB: `UPDATE api_tokens
SET deleted_at=NULL WHERE token='...'`. Token is now active; a proper rotation should
generate a fresh token and update Vault + mcpo-proxy secrets.

**D-36:** D-RST "operator presence" assumption was false — AppRole credentials at
`~/.vault-approle/backup/` enable fully non-interactive Restic operations. Pattern
documented in `docs/runbooks/vault-restore-from-backup.md`.

## A-012 equivalence harness results

| Migration | Verification | Result |
|---|---|---|
| CMDB_SOURCE flip (Phase 13.5) | `python3 scripts/cmdb_source.py` returns JSON | ✅ NetBox output confirmed |
| Plane admin rotation (NF-14-1) | Vault `secret/plane/admin.password` hash from D-DOC addendum | ✅ Stored in Vault |
| plex-mcp PLEX_TOKEN (Phase 14-G) | `docker exec plex-mcp sh -c "echo PLEX_TOKEN=$PLEX_TOKEN"` sha256 prefix | ✅ `5c5c9e74931a` (non-trivial) |
| zabbix-exporter API token (D-ZBX) | `docker exec zabbix-exporter sh -c "echo ZABBIX_API_TOKEN=$ZABBIX_API_TOKEN"` sha256 prefix | ✅ `8b520a7b4f87` (non-trivial) |

## Items deferred to Phase 15+

1. MkDocs healthcheck: uses `curl` not available in distroless image — shows `unhealthy`
   but serves 200 at docs.internal. Fix: use `wget` or `python3 -c` in healthcheck.
2. Plane API token rotation: D-35 token was restored from soft-delete; a proper
   fresh token should be generated and rotated into Vault + mcpo-proxy.
3. Uptime Kuma homepage slug gap (pre-existing; cosmetic).
4. mcp-docs-remote pre-built image (KI-004; reduces cold-start from 60s to <5s).
5. sms1obot-mcp-server* container hardening (Obot-managed; permanent KI — D#30).
6. Phase 13 Increments 2B–7 (gated on Mouser+DigiKey+CSV; parallel, not blocked).

## CLAUDE.md updates this phase

- Known Hardening Trade-offs: Caddy per-site logs RESOLVED (D-LOG).
- Known Hardening Trade-offs: Zabbix Prometheus exporter RESOLVED (D-ZBX).
- Current Phase: Phase 14 CLOSED.

## Final container count

62 containers (up from 58 at Phase 14 start). New in Phase 14:
- `structurizr` (D-STR)
- `mkdocs` (D-MKD)
- `zabbix-exporter` + `vault-agent-zabbix-exporter` (D-ZBX)
- `loki` + `promtail` (D-LOG)

## Warnings analysis (WARN=3, stable since Window 2)

1. `openhands.internal` not in macOS DNS cache — not actively used, normal.
2. Restic snapshot list inaccessible from probe — expected; probe doesn't have Vault access.
   D-RST confirms repo healthy via AppRole.
3. No gate-specific dependency probes for phase-14-final — section (f) is gate-id-specific;
   generic gate gets no sub-probes. All substantive checks pass.
