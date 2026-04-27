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
