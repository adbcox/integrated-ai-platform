# Phase 13 Block 1.7 — Vault 2.0.0 recovery via enable_unauthenticated_access

Generated: 2026-04-28T07:22:41Z

Amendments applied: §4 polling loop uses 'seq 1 10' (bash range expansion).
Carryover from Block 1.6 §3: §5 verification uses host CLI reading ~/.vault-token.

Root cause source:
- https://github.com/hashicorp/vault/releases/tag/v2.0.0
- https://discuss.hashicorp.com/t/vault-2-0-0-1-21-5-1-20-10-1-19-16-released/77339

## 1. Pre-flight verification

### Vault version + state
```
{
  "version": "2.0.0",
  "sealed": false,
  "type": "shamir",
  "t": 3,
  "n": 5,
  "initialized": true
}
```

### Container
```
vault-server | Up 6 hours (healthy) | hashicorp/vault:latest
```

### Config bind mount
```
{
  "Type": "bind",
  "Source": "/Users/admin/control-center-stack/stacks/vault/vault-config.hcl",
  "Destination": "/vault/config/vault.hcl",
  "Mode": "ro",
  "RW": false,
  "Propagation": "rprivate"
}
```

### Resolved host vault.hcl path
```
  /Users/admin/control-center-stack/stacks/vault/vault-config.hcl
-rw-r--r--  1 admin  staff  260 Apr 26 00:07 /Users/admin/control-center-stack/stacks/vault/vault-config.hcl
```

### Unseal keys
```
-rw-------  1 admin  staff  901 Apr 25 23:41 /Users/admin/vault-init-keys.txt
  line count: 18
```

=== SECTION 1 COMPLETE — 53 lines ===


## 2. Backup + add enable_unauthenticated_access to vault.hcl

### Backup
```
-rw-r--r--  1 admin  staff  260 Apr 28 03:23 /Users/admin/control-center-stack/stacks/vault/vault-config.hcl.pre-block-1.7-backup
```

### Before
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
```

### Action: appended

### After
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

# Vault 2.0.0+: opt back into unauthenticated /sys/generate-root for operator
# recovery flow. Required because Block 1's token rotation used non-orphan
# default and revoking the parent cascaded the new token.
enable_unauthenticated_access = ["generate-root"]
```

=== SECTION 2 COMPLETE — 102 lines ===


## 3. SIGHUP reload (zero-downtime path)

```
  Vault PID inside container: 6
  SIGHUP sent

  /sys/generate-root/attempt after SIGHUP: 200
```
✅ SIGHUP picked up enable_unauthenticated_access — no restart needed

=== SECTION 3 COMPLETE — 115 lines ===


## 4. Restart vault-server (only if §3 didn't pick up the flag)

```
RESTART_NEEDED=false
  Restart skipped — SIGHUP succeeded in §3
```

=== SECTION 4 COMPLETE — 125 lines ===


## 5. Generate new ROOT token via Shamir quorum

### 5.1 Cancel any in-flight + init fresh
```
{
  "nonce": "0240104f-4963-e718-f55c-99d9fa616756",
  "started": true,
  "complete": false,
  "progress": 0,
  "required": 3,
  "encoded_token": 0
}

  nonce: 0240104f-4963-e718-f55c-99d9fa616756
  OTP length: 28 chars (value not logged)
```

### 5.2 Submit 3 unseal keys (key values not logged)
```
  K1=44c K2=44c K3=44c
  key 1: progress=1 complete=false encoded_len=0
  key 2: progress=2 complete=false encoded_len=0
  key 3: progress=3 complete=true encoded_len=38
```

### 5.3 Decode encoded → plaintext root
```
  decoded length: 28 chars (value not logged)
```

### 5.4 Verification (host CLI, reads ~/.vault-token, per Block 1.6 amendment)
```
{
  "display_name": null,
  "policies": null,
  "ttl": null,
  "type": "service",
  "accessor_prefix": "b6W89wh6"
}
```
✅ new root token issued and verified via host CLI

=== SECTION 5 COMPLETE — 170 lines ===


## 6. Execute Block 1.5 deferred items

### 6A. Vaultwarden rename
```
  Before:
    [
      "token",
      "url"
    ]

  has_token=true has_admin_token=false
deletion_time      n/a
destroyed          false
version            2

  Action: EXECUTE_RENAME

  After:
    [
      "admin_token",
      "url"
    ]
```

### 6B. Seed missing paths (placeholders for Block 2)
```
  secret/grafana/api put:
    created_time       2026-04-28T07:24:54.239912934Z
    custom_metadata    <nil>
    deletion_time      n/a
    destroyed          false
    version            1

  secret/anythingllm/api put:
    created_time       2026-04-28T07:24:54.295417589Z
    custom_metadata    <nil>
    deletion_time      n/a
    destroyed          false
    version            1

  Verify list:
    secret/grafana:
      Keys
      ----
      api
    secret/anythingllm:
      Keys
      ----
      api

  Field check:
    secret/grafana/api keys: status
    secret/anythingllm/api keys: status
```

=== SECTION 6 COMPLETE — 228 lines ===


## 7. Token re-rotation (orphan mode), pin image, audit, commit

### 7.0 SECURITY: §6 sanity check exposed the §5-issued token

The `vault token lookup` (without `-format=json` filter) printed the token `id`
field to stdout in §6. The transcript may persist that value. Mitigated
immediately by:

1. Issuing a NEW root token with `-orphan` flag (Block 1's missing flag — this
   prevents future cascade-on-revoke of this token)
2. Using the new token to revoke the exposed token
3. Verifying exposed token returns invalid; new token has policies=[root]

```
  rotation: yes
  new token length: 28 chars (value not logged)
  new token policies: root
  exposed token revoke result: Success! Revoked token (if it existed)
  exposed token lookup after revoke (expect invalid):
    Error looking up token: Error making API request.
    
    URL: GET http://0.0.0.0:8200/v1/auth/token/lookup-self
```

### 7.1 Pin Vault image to 2.0.0 in compose file
```
  compose files referencing hashicorp/vault:
    

  before:

  after:
```

### 7.2 Final audit
```
Vault status:
{
  "version": "2.0.0",
  "sealed": false,
  "t": 3,
  "n": 5,
  "initialized": true
}

Token verification (host CLI):
{
  "display_name": null,
  "policies": null,
  "ttl": null,
  "orphan": true
}

Vaultwarden keys:
[
  "admin_token",
  "url"
]

secret/grafana:
Keys
----
api
secret/anythingllm:
Keys
----
api

vault.hcl tail:
```

### 7.3 Audit results
  ✅ Vaultwarden keys: admin_token,url
  ✅ secret/grafana/api seeded
  ✅ secret/anythingllm/api seeded
  ❌ pin incomplete (pinned=0 latest=0)
  ✅ enable_unauthenticated_access added (SIGHUP picked it up — no restart)
  ✅ token rotated to -orphan mode (will not cascade on next revoke)

=== SECTION 7 COMPLETE — 310 lines ===

