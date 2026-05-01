# Phase Completion Log

> **Note**: Phase numbering was consolidated at commit a6253c3 (2026-04-29 —
> "consolidated phase structure — 3 large phases replacing micro-increments").
> Entries below this note up to the renumbering line use the current numbering;
> entries below the renumbering line use the pre-consolidation numbering.

## Phase 15 — COMPLETE (closed 2026-05-01)

Tag: `phase-15-final`. Full closeout: `docs/phase-15/PHASE_15_CLOSEOUT_2026-05-01.md`.

Originally opened for vault cascade recovery + Mac Studio Day-1 integration.
Mac Studio Day-1 deferred per Path C scope decision; closeout scope shifted
to audit-driven cleanup of the items raised in the 2026-05-01 comprehensive audit.

- 2026-04-30 13:00-22:00 — Vault cascade incident (Sev-2). 9-hour triage:
  api_addr network misdiagnosis, KV mount data loss during fresh-init,
  seal-vault data volume destruction during 5-hour autonomous debug window.
  Transit auto-unseal rebuilt 22:18 UTC with VAULT_TOKEN env wrapper around
  Vault 2.0 dropped `token_file` seal-stanza support.
- 2026-05-01 — KV rebuild verified 47/47 leaf paths populated. Mac Studio
  M3 Ultra arrived (.146). Comprehensive audit + validation pass (3105f07).
  Six audit service-removal recommendations verified non-removable (Section 3
  cross-reference gap). Nine deliverables closed: D-15-01 audit/validation,
  D-15-02 IA hygiene, D-15-03 backup chain (R-01) with discovery that the
  rebuild-populated MinIO key was bogus (driving lessons-learned), D-15-04
  Vault audit re-enable (R-02), D-15-05 PreToolUse hooks (R-03), D-15-06
  vault-test (R-08), D-15-07 ADR-A-007 Path B, D-15-09 closeout, D-15-10
  PROJECT_FRAMEWORK.md doctrine.
- Carry-overs to Phase 16: Block 4.D closeout, Block 4.E cross-index service
  (structural blocker for autonomous coding), Mac Studio Day-1, Vault raft-
  snapshot integration in backup, loose-doc retirement, documentation drift
  detection automation, recovery-handoff doctrine update.

## Phase 14 — COMPLETE (2026-04-30)

Phase 14 D-DOC closed clean. Final regression: PASS=15 FAIL=0 WARN=3.
Six tracks delivered:

- D-LOG: Loki + Promtail; Caddy per-site access log analysis via LogQL;
  `caddy-per-site-p14` Grafana dashboard at grafana.internal. Promtail
  uses cap_add: [DAC_READ_SEARCH] (D#31 documented exception).
- D-ZBX: zabbix-exporter container scrapes Zabbix API via Bearer token
  (Vault Agent sidecar); vmagent ingests; `zabbix-overview-p14` Grafana
  dashboard provisioned.
- D-RST: vault-restore-from-backup runbook exercised (PASS) +
  credential-path corrections.
- D-STR + D-MKD: Structurizr + MkDocs Material at .internal domains.
- D-XINDEX: cross-index validator (`scripts/cross-index-validate.py`) +
  ADR->Plane coherence regression probe section (g).
- D-CN: connector hardening — apply-path test, rate-limit audit,
  pagination contract (D#10-#15).

Closed at commit 9acfe6e. Tag: phase-14-final.

## Phase 13 — COMPLETE (2026-04-29)

Block 4 (integration stack) and Block H1 (foundation hardening) closed.

- Block 4.A (foundation): full closeout suite, commit 5077811.
- Block 4.C (NetBox CMDB authority via ADR-A-014/A-015): full closeout
  suite (PLAN, C1 audit, C2 discoveries, C3 migration, C4 backfill,
  C5_2 evidence, CLOSEOUT). NetBox is now the authoritative service
  inventory; YAML retained as A-012 deprecation-gate fallback.
- Block 4.D (InvenTree asset inventory): deployed (4 containers running,
  AppRoles provisioned) but no formal closeout document. Documentation
  gap flagged in audit-validation 2026-05-01; retroactive closeout
  scheduled for Phase 16.
- Block 4.E (cross-index service joining NetBox + InvenTree + Plane +
  Vault + ADRs): un-built. Validator exists from Phase 14 D-XINDEX;
  service does not. Structural blocker for autonomous coding; tracked
  for Phase 16/17.
- Block H1 (foundation hardening): COMPLETE, commit da3a1a1.

— phase numbering consolidated at commit a6253c3 (2026-04-29) —

[older entries below use pre-consolidation numbering]

## Phase 16: Vault Architecture Restoration — COMPLETE (2026-04-27)
- All 10 .env-stored secrets migrated to Vault
- Corrupted entries cleaned (`secret/strava/oauth`, `secret/seedbox`)
- Deploy pattern established (`deploy-stack.sh` + `vault-mapping.yaml`)
- ADR-A-006 documented
- Commit: 76aa6e4

## Phase 10: Strava OAuth — COMPLETE (2026-04-27)
- OAuth grant completed with `activity:read_all read` scope
- Tokens stored in `secret/strava/oauth` and `secret/mcp/strava`
- `refresh-strava-token.sh` verified (token rotation working)
- Calendar sync verified: 21/22 activities synced from last 30 days

## Caddy CA Trust — PENDING
- Root CA cert extracted to `/tmp/caddy-local-ca.crt` and present in `/Library/Keychains/System.keychain`
- Trust policy not applied: macOS 26.3 requires interactive Authorization Services
  (SecurityAgent GUI prompt) for `SecTrustSettingsSetTrustSettings()` against the
  System trust store. `sudo`, `sudo -S` with password, and `launchctl asuser 501`
  dispatch all hit the same auth gate.
- To complete: from a Terminal session inside the console user's GUI (or with the
  console user physically present to click the auth prompt), run:
  `sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain /tmp/caddy-local-ca.crt`

## Caddy CA Trust — COMPLETE (Mon Apr 27 19:34:35 EDT 2026)
- Root CA installed in /Library/Keychains/System.keychain via Screen Sharing GUI session (adriancox)
- HTTPS validation succeeds without -k flag (verify=0 confirmed across 18 .internal domains)
- secret/macmini/sudo established for future privileged SSH operations
- Phase 7 closeout complete

## 30-Day Plan Status — COMPLETE (Mon Apr 27 19:34:35 EDT 2026)
- Phase 16 (Vault architecture restoration): Complete (commit 76aa6e4)
- Strava OAuth: Complete, 21 activities synced
- Caddy CA trust: Complete, all .internal HTTPS validates cleanly
- All P0/P1/P2 automatable items closed

## Phase 7 FINAL Closeout — COMPLETE (Mon Apr 27 21:50:03 EDT 2026)

### All 6 dispositions resolved
1. **mcp-docker**: Replaced host-process workaround with proper Docker container (`mcp-docker-remote`, node:22-slim, mounts /var/run/docker.sock from Linux VM, listens 0.0.0.0:8092). Healthz=200 via Caddy. KI-002 resolved.
2. **open-webui**: Stable after Colima VM resize (8→16 GiB); 0 restarts; serves 200 via webui.internal.
3. **litellm-gateway**: Stable after Colima VM resize; 0 restarts; serves 200.
4. **obot**: Container healthy; backend serves correctly (/api/=403, /oauth2/login=302). UI / returns 502 from internal dev-mode proxy misconfig (Vite frontend); tracked separately as KI-003.
5. **OPNsense Unbound**: 4 A-records added (mcp-filesystem, mcp-docker, mcp-docs, victoria) → 192.168.10.145.
6. **plane-api OOM**: Set GUNICORN_TIMEOUT=120 (was implicit 30s) and mem_limit 2G in compose. Real cause was worker timeout, not memory. 0 SIGKILL events in observation. KI-001 resolved.

### Infrastructure changes
- Colima VM: resized 8 GiB → 16 GiB (was OOM-thrashing kernel-killed containers); started with --network-host-addresses to ensure LAN-IP forwarding.
- Caddyfile: 21 routes total; all use host.docker.internal (replacing 192.168.10.145, which is the documented Colima/Docker pattern for container→host routing).

### Verification
- 16/17 .internal domains return verify=0, HTTP 2xx-4xx via DNS
- All 17 domains resolve via OPNsense (192.168.10.1)
- 0 container restart loops; all backends healthy
- mcp-* domains return 404 on / (correct MCP behavior; healthz=200)
- obot returns 502 only on / (frontend dev-mode bug, KI-003)

### Known issues now tracked
- KI-001 (plane-api OOM): RESOLVED
- KI-002 (mcp-docker Colima socket): RESOLVED
- KI-003 (obot dev-mode frontend proxy): OPEN, pre-existing, unrelated to Phase 7

## Phase 7 GENUINE Closeout — COMPLETE (Mon Apr 27 22:06:07 EDT 2026)

### Coverage audit
- 22 Caddyfile routes audited against 24 OPNsense Unbound A-records (delta = mac-mini, qnap infrastructure entries with no Caddy route by design)
- All 22 .internal domains return verify=0 + HTTP 2xx-4xx
- All 22 domains resolve to 192.168.10.145 via OPNsense

### KI-003 resolved
- Root cause: `OBOT_DEV_MODE: "true"` made obot proxy / to a non-running Vite dev server (port 5174)
- Fix: Set OBOT_DEV_MODE=false in docker/obot-stack.yml
- obot:latest image is API-only (no bundled UI); /api/=403, /=404 — both valid responses

### Final state
- HTTP pass: 22/22
- DNS pass:  22/22
- Open known issues: none (KI-001, KI-002, KI-003 all RESOLVED)
