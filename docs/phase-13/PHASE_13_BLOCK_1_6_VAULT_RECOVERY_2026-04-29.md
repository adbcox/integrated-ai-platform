# Phase 13 Block 1.6 — Vault auth recovery

Generated: 2026-04-28T07:11:50Z

Amendment applied: Section 3 verification uses host CLI reading from ~/.vault-token
(catches token-handoff mismatch in §3 rather than failing downstream in §4)

## 1. Clear stale auth state

### Forensic preserve + clear
```
  preserved: ~/.vault-token.invalid-20260428-031208 (       0 bytes)
  VAULT_TOKEN env: (unset)
ls: /Users/admin/.vault-token: No such file or directory
```

### Unauthenticated probe — /v1/sys/seal-status
```
{
  "type": "shamir",
  "sealed": false,
  "version": "2.0.0",
  "t": 3,
  "n": 5,
  "progress": 0,
  "initialized": true
}
```

### Decision
```
  ❌ /sys/seal-status returned unexpected response — fallback diagnostics
     needed.
```

=== SECTION 1 COMPLETE — 34 lines ===


## 2. Locate unseal keys

```
  Init file: /Users/admin/vault-init-keys.txt
-rw-------  1 admin  staff  901 Apr 25 23:41 /Users/admin/vault-init-keys.txt
  line count: 18

  Format pattern (first 3 words per line, redacts key bytes):
    L1: Unseal Key 1:
    L2: Unseal Key 2:
    L3: Unseal Key 3:
    L4: Unseal Key 4:
    L5: Unseal Key 5:
    L6:
    L7: Initial Root Token:
    L8:
    L9: Vault initialized with
    L10: distribute the key
```

=== SECTION 2 COMPLETE — 57 lines ===


## 3. Generate new root token via Shamir quorum (unauthenticated)

### 3.1 generate-root -init
```
  init response (redacted otp value):
{
  "nonce": null,
  "otp_length": null,
  "started": null,
  "complete": null,
  "encoded_token": 0
}

  nonce captured:
  OTP length: 0 chars
```

❌ BLOCKED: generate-root init failed
```
{"errors":["permission denied"]}
```

### 3.2 Submit unseal keys (3 of 5)
```
  K1=44c K2=44c K3=44c
  key 1: progress=0 complete=false encoded_len=0
  key 2: progress=0 complete=false encoded_len=0
  key 3: progress=0 complete=false encoded_len=0
```
❌ BLOCKED: 3 keys submitted but no encoded_token returned

=== SECTION 3 COMPLETE — 91 lines ===


## 4. Execute Block 1.5 deferred items

### 4A. Vaultwarden rename (token → admin_token)
```
Current keys:

  has_token= has_admin_token=

Action: MISSING_BOTH

After:
```

### 4B. Seed missing paths
```
secret/grafana/api:

URL: GET http://0.0.0.0:8200/v1/sys/internal/ui/mounts/secret/grafana/api
Code: 403. Errors:

* permission denied

secret/anythingllm/api:

URL: GET http://0.0.0.0:8200/v1/sys/internal/ui/mounts/secret/anythingllm/api
Code: 403. Errors:

* permission denied

Verify:
Error making API request.

URL: GET http://0.0.0.0:8200/v1/sys/internal/ui/mounts/secret/grafana
Code: 403. Errors:

* permission denied
---
Error making API request.

URL: GET http://0.0.0.0:8200/v1/sys/internal/ui/mounts/secret/anythingllm
Code: 403. Errors:

* permission denied

Field check:
  secret/grafana/api keys:
  secret/anythingllm/api keys:
```

=== SECTION 4 COMPLETE — 143 lines ===


## 5. FALLBACK — Vault gates /sys/generate-root/* but not /sys/seal-status

### Symptom

- `PUT /v1/sys/seal-status` (no auth): **200** — JSON returned, sealed=false
- `PUT /v1/sys/generate-root/attempt` (no auth): **403 permission denied**

Standard Vault treats both as unauthenticated. This Vault has the recovery
flow gated. Per directive: capture diagnostics, STOP, do NOT restart.

### Diagnostic 1: vault.hcl
```hcl
storage "file" {
  path = "/vault/data"
}

listener "tcp" {
  address     = "0.0.0.0:8200"
  tls_disable = 1
}

api_addr      = "http://192.168.10.145:8200"
ui            = true
disable_mlock = true   # required: mlock not available in macOS/Colima containers
storage "file" {
  path = "/vault/data"
}

listener "tcp" {
  address     = "0.0.0.0:8200"
  tls_disable = 1
}

api_addr      = "http://192.168.10.145:8200"
ui            = true
disable_mlock = true   # required: mlock not available in macOS/Colima containers
```

### Diagnostic 2: docker logs vault-server --tail 50
```
2026-04-28T06:08:37.459Z [INFO]  core: updated replicated hwm role and managed key counts: prefix=replicated/ currentMonth="2026-04-28 06:08:37.458052333 +0000 UTC"
2026-04-28T06:08:37.462Z [INFO]  core: updated replicated max kv counts: prefix=replicated/ currentMonth="2026-04-28 06:08:37.458052333 +0000 UTC"
2026-04-28T06:08:37.462Z [INFO]  core: updated local max role and managed key counts: prefix=local/ currentMonth="2026-04-28 06:08:37.458052333 +0000 UTC"
2026-04-28T06:08:37.462Z [INFO]  core: updated local max kv counts: prefix=local/ currentMonth="2026-04-28 06:08:37.458052333 +0000 UTC"
2026-04-28T06:08:37.463Z [INFO]  core: updated local max external plugin counts: prefix=local/ currentMonth="2026-04-28 06:08:37.458052333 +0000 UTC"
2026-04-28T06:08:37.463Z [INFO]  core: updated local kmip enabled: prefix=local/ currentMonth="2026-04-28 06:08:37.458052333 +0000 UTC"
2026-04-28T06:08:37.464Z [INFO]  core: updated cluster data protection call counts: prefix=local/ currentMonth="2026-04-28 06:08:37.458052333 +0000 UTC"
2026-04-28T06:18:37.459Z [INFO]  core: updated replicated hwm role and managed key counts: prefix=replicated/ currentMonth="2026-04-28 06:18:37.457813481 +0000 UTC"
2026-04-28T06:18:37.462Z [INFO]  core: updated replicated max kv counts: prefix=replicated/ currentMonth="2026-04-28 06:18:37.457813481 +0000 UTC"
2026-04-28T06:18:37.462Z [INFO]  core: updated local max role and managed key counts: prefix=local/ currentMonth="2026-04-28 06:18:37.457813481 +0000 UTC"
2026-04-28T06:18:37.463Z [INFO]  core: updated local max kv counts: prefix=local/ currentMonth="2026-04-28 06:18:37.457813481 +0000 UTC"
2026-04-28T06:18:37.464Z [INFO]  core: updated local max external plugin counts: prefix=local/ currentMonth="2026-04-28 06:18:37.457813481 +0000 UTC"
2026-04-28T06:18:37.464Z [INFO]  core: updated local kmip enabled: prefix=local/ currentMonth="2026-04-28 06:18:37.457813481 +0000 UTC"
2026-04-28T06:18:37.464Z [INFO]  core: updated cluster data protection call counts: prefix=local/ currentMonth="2026-04-28 06:18:37.457813481 +0000 UTC"
2026-04-28T06:28:37.457Z [INFO]  core: updated replicated hwm role and managed key counts: prefix=replicated/ currentMonth="2026-04-28 06:28:37.457630692 +0000 UTC"
2026-04-28T06:28:37.458Z [INFO]  core: updated replicated max kv counts: prefix=replicated/ currentMonth="2026-04-28 06:28:37.457630692 +0000 UTC"
2026-04-28T06:28:37.458Z [INFO]  core: updated local max role and managed key counts: prefix=local/ currentMonth="2026-04-28 06:28:37.457630692 +0000 UTC"
2026-04-28T06:28:37.458Z [INFO]  core: updated local max kv counts: prefix=local/ currentMonth="2026-04-28 06:28:37.457630692 +0000 UTC"
2026-04-28T06:28:37.459Z [INFO]  core: updated local max external plugin counts: prefix=local/ currentMonth="2026-04-28 06:28:37.457630692 +0000 UTC"
2026-04-28T06:28:37.459Z [INFO]  core: updated local kmip enabled: prefix=local/ currentMonth="2026-04-28 06:28:37.457630692 +0000 UTC"
2026-04-28T06:28:37.459Z [INFO]  core: updated cluster data protection call counts: prefix=local/ currentMonth="2026-04-28 06:28:37.457630692 +0000 UTC"
2026-04-28T06:38:37.458Z [INFO]  core: updated replicated hwm role and managed key counts: prefix=replicated/ currentMonth="2026-04-28 06:38:37.457664952 +0000 UTC"
2026-04-28T06:38:37.462Z [INFO]  core: updated replicated max kv counts: prefix=replicated/ currentMonth="2026-04-28 06:38:37.457664952 +0000 UTC"
2026-04-28T06:38:37.462Z [INFO]  core: updated local max role and managed key counts: prefix=local/ currentMonth="2026-04-28 06:38:37.457664952 +0000 UTC"
2026-04-28T06:38:37.462Z [INFO]  core: updated local max kv counts: prefix=local/ currentMonth="2026-04-28 06:38:37.457664952 +0000 UTC"
2026-04-28T06:38:37.463Z [INFO]  core: updated local max external plugin counts: prefix=local/ currentMonth="2026-04-28 06:38:37.457664952 +0000 UTC"
2026-04-28T06:38:37.463Z [INFO]  core: updated local kmip enabled: prefix=local/ currentMonth="2026-04-28 06:38:37.457664952 +0000 UTC"
2026-04-28T06:38:37.463Z [INFO]  core: updated cluster data protection call counts: prefix=local/ currentMonth="2026-04-28 06:38:37.457664952 +0000 UTC"
2026-04-28T06:48:37.459Z [INFO]  core: updated replicated hwm role and managed key counts: prefix=replicated/ currentMonth="2026-04-28 06:48:37.458167477 +0000 UTC"
2026-04-28T06:48:37.461Z [INFO]  core: updated replicated max kv counts: prefix=replicated/ currentMonth="2026-04-28 06:48:37.458167477 +0000 UTC"
2026-04-28T06:48:37.462Z [INFO]  core: updated local max role and managed key counts: prefix=local/ currentMonth="2026-04-28 06:48:37.458167477 +0000 UTC"
2026-04-28T06:48:37.462Z [INFO]  core: updated local max kv counts: prefix=local/ currentMonth="2026-04-28 06:48:37.458167477 +0000 UTC"
2026-04-28T06:48:37.462Z [INFO]  core: updated local max external plugin counts: prefix=local/ currentMonth="2026-04-28 06:48:37.458167477 +0000 UTC"
2026-04-28T06:48:37.462Z [INFO]  core: updated local kmip enabled: prefix=local/ currentMonth="2026-04-28 06:48:37.458167477 +0000 UTC"
2026-04-28T06:48:37.463Z [INFO]  core: updated cluster data protection call counts: prefix=local/ currentMonth="2026-04-28 06:48:37.458167477 +0000 UTC"
2026-04-28T06:49:12.674Z [INFO]  expiration: revoked lease: lease_id=auth/token/root/he384a2440a3516cdcc5b55c2b1114ce45646f283c8ddebd0ceaaede5d34265f5
2026-04-28T06:58:37.458Z [INFO]  core: updated replicated hwm role and managed key counts: prefix=replicated/ currentMonth="2026-04-28 06:58:37.458525976 +0000 UTC"
2026-04-28T06:58:37.459Z [INFO]  core: updated replicated max kv counts: prefix=replicated/ currentMonth="2026-04-28 06:58:37.458525976 +0000 UTC"
2026-04-28T06:58:37.459Z [INFO]  core: updated local max role and managed key counts: prefix=local/ currentMonth="2026-04-28 06:58:37.458525976 +0000 UTC"
2026-04-28T06:58:37.459Z [INFO]  core: updated local max kv counts: prefix=local/ currentMonth="2026-04-28 06:58:37.458525976 +0000 UTC"
2026-04-28T06:58:37.460Z [INFO]  core: updated local max external plugin counts: prefix=local/ currentMonth="2026-04-28 06:58:37.458525976 +0000 UTC"
2026-04-28T06:58:37.460Z [INFO]  core: updated local kmip enabled: prefix=local/ currentMonth="2026-04-28 06:58:37.458525976 +0000 UTC"
2026-04-28T06:58:37.460Z [INFO]  core: updated cluster data protection call counts: prefix=local/ currentMonth="2026-04-28 06:58:37.458525976 +0000 UTC"
2026-04-28T07:08:37.459Z [INFO]  core: updated replicated hwm role and managed key counts: prefix=replicated/ currentMonth="2026-04-28 07:08:37.458923004 +0000 UTC"
2026-04-28T07:08:37.459Z [INFO]  core: updated replicated max kv counts: prefix=replicated/ currentMonth="2026-04-28 07:08:37.458923004 +0000 UTC"
2026-04-28T07:08:37.459Z [INFO]  core: updated local max role and managed key counts: prefix=local/ currentMonth="2026-04-28 07:08:37.458923004 +0000 UTC"
2026-04-28T07:08:37.459Z [INFO]  core: updated local max kv counts: prefix=local/ currentMonth="2026-04-28 07:08:37.458923004 +0000 UTC"
2026-04-28T07:08:37.460Z [INFO]  core: updated local max external plugin counts: prefix=local/ currentMonth="2026-04-28 07:08:37.458923004 +0000 UTC"
2026-04-28T07:08:37.460Z [INFO]  core: updated local kmip enabled: prefix=local/ currentMonth="2026-04-28 07:08:37.458923004 +0000 UTC"
2026-04-28T07:08:37.460Z [INFO]  core: updated cluster data protection call counts: prefix=local/ currentMonth="2026-04-28 07:08:37.458923004 +0000 UTC"
```

### Diagnostic 3: env (sensitive values redacted)
```
[
  "VAULT_LOG_LEVEL=info",
  "SKIP_SETCAP=true",
  "VAULT_ADDR=http://0.0.0.0:8200",
  "VAULT_API_ADDR=http://192.168.10.145:8200",
  "PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
  "NAME=vault"
]
```

### Diagnostic 4: listener config from Vault config dump (auth method)
```
vault.hcl
---
=== /vault/config/vault.hcl ===
storage "file" {
  path = "/vault/data"
}

listener "tcp" {
  address     = "0.0.0.0:8200"
  tls_disable = 1
}

api_addr      = "http://192.168.10.145:8200"
ui            = true
disable_mlock = true   # required: mlock not available in macOS/Colima containers
```

### Endpoint-by-endpoint probe (no auth)
```
  /v1/sys/seal-status -> 200
  /v1/sys/health -> 200
  /v1/sys/init -> 200
  /v1/sys/leader -> 200
  /v1/sys/generate-root/attempt -> 403
```

### Status: BLOCKED on user-driven recovery

Did NOT attempt:
- `docker stop vault-server` (per directive: requires explicit approval)
- Container-restart in recovery mode
- Any modification to vault config

What needs user-driven action:

1. **Inspect** the listener config (above diagnostic) for any custom policy
   blocking `/sys/generate-root`. Standard Vault has these unauthenticated.
   If something custom is there, edit the config to allow generate-root and
   reload (no restart needed: `vault reload` works on hot-reloaded configs).

2. **OR**: `docker restart vault-server` with auth-gating env var removed.
   ~30 sec downtime; Vault will be sealed on restart so unseal keys needed.

3. **OR**: Side-channel root token. If anyone else has a working root token
   (not the one in ~/.vault-token.invalid-* — that's confirmed dead), use it
   to manually re-execute Block 1.5 §1 + §2.

### Status of Block 1.5 deferred items

Still deferred — Block 1.6 was unable to restore root access without restart:
- Vaultwarden `token` → `admin_token` rename: status unknown
- `secret/grafana/api` placeholder seed: not created
- `secret/anythingllm/api` placeholder seed: not created

### Mitigation guidance carried forward (for next rotation)

Use `vault token create -orphan -policy=root -ttl=720h`. The `-orphan` flag
makes the new token NOT a child of the creating token. Then revoking the old
token will not cascade to the new one.


=== SECTION 5 (FALLBACK) COMPLETE — 313 lines ===
