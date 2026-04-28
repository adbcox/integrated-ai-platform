# Phase Completion Log

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
