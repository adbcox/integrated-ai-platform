# Vault test instance — operational runbook

**Status**: Active. Stood up 2026-05-01 closing audit R-08 / D-15-06.
**Container**: `vault-test` (compose at `docker/vault-test/docker-compose.yml`)
**Endpoint**: `http://127.0.0.1:8210` (host) or `http://vault-test:8200` (container network)
**Root token**: `root-test-token` (well-known, non-secret — this is a test instance)

---

## Purpose

Ephemeral Vault instance for safely rehearsing destructive Vault operations before running them on production. Designed in response to the 2026-04-30 Vault cascade incident (Sev-2): a fresh-init was run against production Vault during recovery, wiping the entire KV mount. With this test instance, that operation can be rehearsed safely against vault-test, validated, and only then run on prod with confidence.

## Architecture

- **Image**: `hashicorp/vault:latest` — same as prod for behavioral parity
- **Mode**: `server -dev` — in-memory storage, single-shard auto-unsealed at startup
- **Network**: isolated bridge `vault-test-net` (no overlap with prod `control-center-net`)
- **Persistence**: none — restart wipes all state. This is intentional.
- **Capabilities**: cap_drop ALL, SKIP_SETCAP=1 (matches prod hardening posture)
- **Token**: root-test-token (set via VAULT_DEV_ROOT_TOKEN_ID); not a secret, do not migrate to Vault prod

## Access

From the Mac Mini host:
```
export VAULT_ADDR=http://127.0.0.1:8210
export VAULT_TOKEN=root-test-token
vault status
vault kv put secret/test-foo value=bar
vault kv get secret/test-foo
```

From inside another container on `vault-test-net`:
```
VAULT_ADDR=http://vault-test:8200 vault ...
```

The standard `vault` CLI binary works — same commands as prod, just different VAULT_ADDR.

## Lifecycle

**Wipe and restart** (typical between tests):
```
cd ~/repos/integrated-ai-platform/docker/vault-test
docker compose restart vault-test
```

State is gone. New root token is the same well-known value (root-test-token).

**Stop entirely** (when not in use):
```
docker compose down
```

**Start fresh**:
```
docker compose up -d
```

## Recommended use cases

1. **Rehearse destructive operations** before running them on prod (operator init, audit disable, KV wipes, AppRole resets)
2. **Validate vault-recovery-from-shamir runbook** end-to-end in a contained way — though dev mode does not exercise sealing/unsealing, so for full-fidelity recovery testing, a separate file-backend test instance would be needed (not stood up; tracked as future work)
3. **Equivalence harness staging** — the cross-index validator at `scripts/cross-index-validate.py` and similar can run against vault-test for development before pointing at prod
4. **PreToolUse hook regression** — verify the `scripts/claude-pretooluse-hook.py` correctly blocks dangerous patterns by attempting them against vault-test (the hook blocks regardless of target; this confirms behavior end-to-end)

## What NOT to do

- Do not store production secrets here. Anyone with shell access can read them — the root token is well-known.
- Do not point production services at `http://127.0.0.1:8210` or `vault-test:8200` even temporarily; service discovery should never resolve there.
- Do not enable audit on vault-test expecting it to capture for compliance — the in-memory storage means audit log writes also vanish on restart.

## Future work

A second test instance with file backend (persistent storage, real seal/unseal cycles) would be needed for testing backup-restore workflows and full-fidelity recovery procedures. Tracked as an enhancement; not blocking R-08 closure since dev mode covers the bulk of destructive-op rehearsal.

## References

- `docs/phase-15/COMPREHENSIVE_AUDIT_2026-05-01.md` Section 13 Blocker 3 — original recommendation
- `docs/phase-15/COMPREHENSIVE_AUDIT_VALIDATION_2026-05-01.md` Section 10 — concur on the blocker
- `docs/runbooks/pretooluse-hooks.md` — companion safety gate (D-15-05)
