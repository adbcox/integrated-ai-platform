# Phase 15 — Vault Credential Audit (Post-Recovery)

**Date:** 2026-04-30
**Status:** Recovery R-0 through R-4 assumed complete (vault-server unsealed, KV readable).
**Scope:** Read-only audit of `secret/*` to determine what survived vs. what needs regeneration.
**Time cap:** 30 min total. Surface after audit completes — do NOT regenerate in this window.

---

## Pre-Conditions (Verify Before Starting)

Run these three checks. If any fails, STOP and surface — do not proceed to audit.

```bash
# 1. vault-server is unsealed
docker exec vault-server vault status | grep -E "Sealed|Initialized"
# Expected: Sealed=false, Initialized=true

# 2. Operator root token (or audit-capable token) is available
# Operator places token at /tmp/vault-audit-token (chmod 600)
test -r /tmp/vault-audit-token && echo "TOKEN PRESENT" || echo "TOKEN MISSING"

# 3. KV v2 mount is responsive
export VAULT_ADDR=http://vault-server:8200
export VAULT_TOKEN=$(cat /tmp/vault-audit-token)
vault kv list secret/ 2>&1 | head -20
```

**STOP if:** Any check fails. Surface output to operator.

---

## Audit Execution (≤20 min)

### A-1 — Top-level path inventory (5 min)

```bash
mkdir -p /tmp/vault-audit
vault kv list -format=json secret/ > /tmp/vault-audit/top-level.json 2>&1
vault kv list secret/ > /tmp/vault-audit/top-level.txt 2>&1
cat /tmp/vault-audit/top-level.txt
```

Expected paths (based on platform doctrine): `netbox/`, `plane/`, `grafana/`, `zabbix/`, `nextcloud/`, `vaultwarden/`, `headscale/`, `control-plane/`, `litellm/`, `obot/`, `open-webui/`, `restic/`, `minio/`, `opnsense/`, `mcpo/`, plus per-service AppRole role-ids/secret-ids.

### A-2 — Per-service path walk (10 min)

For each top-level path, list children and record metadata (NOT values):

```bash
for svc in $(vault kv list -format=json secret/ | jq -r '.[]' | sed 's|/$||'); do
  echo "=== secret/$svc ===" >> /tmp/vault-audit/walk.txt
  vault kv list "secret/$svc" >> /tmp/vault-audit/walk.txt 2>&1
  # For each leaf, capture metadata only (created_time, version) — never values
  for leaf in $(vault kv list -format=json "secret/$svc" 2>/dev/null | jq -r '.[]' 2>/dev/null); do
    leaf_clean=$(echo "$leaf" | sed 's|/$||')
    if vault kv list "secret/$svc/$leaf_clean" >/dev/null 2>&1; then
      # subdirectory, skip metadata
      continue
    fi
    echo "  -- $leaf_clean --" >> /tmp/vault-audit/walk.txt
    vault kv metadata get -format=json "secret/$svc/$leaf_clean" 2>&1 \
      | jq '{created_time, current_version, updated_time}' >> /tmp/vault-audit/walk.txt 2>&1
  done
done
```

### A-3 — AppRole role health (5 min)

```bash
vault list auth/approle/role > /tmp/vault-audit/approles.txt 2>&1
for role in $(vault list -format=json auth/approle/role 2>/dev/null | jq -r '.[]'); do
  echo "=== $role ===" >> /tmp/vault-audit/approle-detail.txt
  vault read -format=json "auth/approle/role/$role" \
    | jq '{token_policies, token_ttl, token_max_ttl, secret_id_ttl, bind_secret_id}' \
    >> /tmp/vault-audit/approle-detail.txt 2>&1
done
```

---

## Classification (5 min)

Take `/tmp/vault-audit/walk.txt` and classify each leaf into one of three buckets in this document's "Audit Outcome" section below:

| Bucket | Criteria | Action Required |
|--------|----------|-----------------|
| **INTACT** | Path exists, metadata reads cleanly, version ≥ 1 | None — sidecar render will recover service |
| **MISSING** | Path expected (per doctrine) but `vault kv list` returns no entry | Regenerate — needs targeted prompt |
| **STALE** | Path exists but `created_time` predates the seal-vault incident *and* the credential is one that vault-server cannot independently verify (Postgres pw, Grafana admin pw, etc.) | Re-coordinate with downstream system (DB ALTER USER, etc.) |

**Special cases (mark as MANUAL regardless of bucket):**
- `secret/opnsense/api` — OPNsense issues api_key/secret only via UI
- `secret/vaultwarden/admin` — token issued at first boot, only available from container env
- `secret/headscale/admin` — issued via `headscale apikeys create`, not extractable

---

## Audit Outcome

*Filled in after A-1/A-2/A-3 complete.*

### INTACT (no action needed)
- TBD

### MISSING (needs regeneration prompt)
- TBD

### STALE / DB-coordinated (needs ALTER USER + Vault write)
- TBD

### MANUAL (operator UI/CLI only)
- TBD

### AppRole status
- Total roles: TBD
- Roles with valid secret_id: TBD
- Roles needing secret_id rotation: TBD

---

## Surface Format

When audit completes, output:

```
STATUS: VAULT-AUDIT PASS
INTACT: <count>
MISSING: <count>
STALE: <count>
MANUAL: <count>
APPROLES: <total>, <healthy>, <needs-rotation>
ARTIFACTS: /tmp/vault-audit/{top-level.txt, walk.txt, approles.txt, approle-detail.txt}
NEXT: targeted regeneration prompt for MISSING + STALE only
```

Then halt. Do not regenerate. Do not write to Vault. The next prompt will be operator-issued and scoped to the specific failures this audit identifies.

---

## Hard Constraints (Same as Recovery Handoff)

- Read-only. Zero `vault kv put`, zero `vault write` (except the inert metadata reads above).
- 30-min total cap. If A-2 doesn't finish in 15 min, surface with partial results.
- Never log credential values to any file or stdout. `vault kv get -format=json secret/...` is forbidden — use `vault kv metadata get` only.
- If a path errors with permission-denied, log the path name only and continue. Do not retry with a different token.
