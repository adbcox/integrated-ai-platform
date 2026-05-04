# Runbook — Provision a Vault AppRole + sidecar for a new service

Operator-facing how-to for provisioning the Vault policy + AppRole +
local secret-id files + Vault Agent sidecar config that a new
credential-consuming service needs. Generalises the
`scripts/provision-{buildarr,bazarr,scraparr,cleanuparr}.sh`
pattern. Companion to `docs/architecture-facts/vault-agent-sidecar-pattern.md`,
which carries the *why*; this runbook is the *how*.

## Prerequisites

- Vault is running (`vault-server` container) and unsealed.
- Admin token resolvable via `scripts/lib/vault-admin-token.sh`.
  The helper's lookup precedence (lines 26–30):
  ```
  1. ${VAULT_TOKEN} already exported (CI / operator override)
  2. Newest ~/vault-init-keys-NEW-*.txt (post-rebuild canonical keys file,
     mtime-sorted to survive future rebuilds without code change)
  3. ${HOME}/.vault-token IFF it validates against the live Vault
  ```
  Operator usage from an interactive shell (lines 15–16):
  ```
  source /Users/admin/repos/integrated-ai-platform/scripts/lib/vault-admin-token.sh
  export VAULT_TOKEN=$(resolve_admin_vault_token)
  ```
- The service's secrets already exist at the `secret/<domain>/<name>`
  paths the policy will grant. AppRole provisioning does not create
  secrets; it grants read access to existing ones.
- Working directory is the repo root.

## 1. Author the policy file

Path convention: `config/vault-policies/<service>-policy.hcl`.

Verbatim from `config/vault-policies/buildarr-policy.hcl` (lines 7–21):

```hcl
path "secret/data/arr/radarr" {
  capabilities = ["read"]
}

path "secret/data/arr/prowlarr" {
  capabilities = ["read"]
}

path "secret/data/arr/sonarr" {
  capabilities = ["read"]
}

path "secret/data/arr/sportarr" {
  capabilities = ["read"]
}
```

One `path` block per secret the service must read. Path form is
`secret/data/<domain>/<name>` (KV v2 — note the `/data/` segment).
Capabilities should be `["read"]` only unless the service writes
back; minimal-capability is doctrine.

The policy file is referenced from the provision script as a
relative path. Verbatim from `provision-buildarr.sh` (line 18):

```bash
POLICY_FILE="config/vault-policies/${SERVICE}-policy.hcl"
```

## 2. Write the policy + create the AppRole

The provision script copies the policy into the Vault container and
writes it. Verbatim from `provision-buildarr.sh` (lines 28–31):

```bash
log "step 1: writing Vault policy ${SERVICE}"
${DOCKER} cp "${POLICY_FILE}" vault-server:/tmp/${SERVICE}-policy.hcl
${DOCKER} exec -e VAULT_TOKEN="${VAULT_TOKEN}" vault-server \
  vault policy write ${SERVICE} /tmp/${SERVICE}-policy.hcl
```

Then creates (or updates) the AppRole. Verbatim from
`provision-buildarr.sh` (lines 34–40):

```bash
log "step 2: creating/updating AppRole ${SERVICE}"
${DOCKER} exec -e VAULT_TOKEN="${VAULT_TOKEN}" vault-server \
  vault write auth/approle/role/${SERVICE} \
    token_policies=${SERVICE} \
    token_ttl=1h \
    token_max_ttl=4h \
    secret_id_ttl=0
```

Field meanings:
- `token_policies=${SERVICE}` — references the policy name written
  in step 1.
- `token_ttl=1h` / `token_max_ttl=4h` — short-lived runtime tokens.
- `secret_id_ttl=0` — secret-id does not expire (the secret-id is
  the long-lived bootstrap credential; the token derived from
  AppRole login is the short-lived one).

## 3. Capture role-id + secret-id locally

Path convention: `~/.vault-approle/<service>/{role-id,secret-id}`.
Permissions: directory `0700`, files `0600`.

Verbatim from `provision-buildarr.sh` (lines 16, 43–44):

```bash
APPROLE_DIR="/Users/admin/.vault-approle/${SERVICE}"
...
mkdir -p "${APPROLE_DIR}"
chmod 0700 "${APPROLE_DIR}"
```

Idempotent role-id capture (lines 46–54):

```bash
if [ ! -s "${APPROLE_DIR}/role-id" ]; then
  log "step 3: writing role-id"
  ${DOCKER} exec -e VAULT_TOKEN="${VAULT_TOKEN}" vault-server \
    vault read -field=role_id auth/approle/role/${SERVICE}/role-id \
    > "${APPROLE_DIR}/role-id"
  chmod 0600 "${APPROLE_DIR}/role-id"
else
  log "step 3: role-id already present (skipping)"
fi
```

Idempotent secret-id capture (lines 56–65):

```bash
if [ ! -s "${APPROLE_DIR}/secret-id" ]; then
  log "step 3: writing secret-id"
  ${DOCKER} exec -e VAULT_TOKEN="${VAULT_TOKEN}" vault-server \
    vault write -force -field=secret_id \
      auth/approle/role/${SERVICE}/secret-id \
    > "${APPROLE_DIR}/secret-id"
  chmod 0600 "${APPROLE_DIR}/secret-id"
else
  log "step 3: secret-id already present (skipping)"
fi
```

Idempotency contract: re-running the script does NOT mint a new
secret-id once one is captured. To rotate, delete the file first.

## 4. Author the Vault Agent sidecar config

Two files, both under `docker/vault-agent-<service>/`:

### 4.1 `agent.hcl`

Verbatim from `docker/vault-agent-buildarr/agent.hcl` (lines 1–29,
file is 29 lines total):

```hcl
pid_file = "/tmp/agent.pid"

vault {
  address = "http://vault-server:8200"
}

auto_auth {
  method "approle" {
    mount_path = "auth/approle"
    config = {
      role_id_file_path                   = "/vault/approle/role-id"
      secret_id_file_path                 = "/vault/approle/secret-id"
      remove_secret_id_file_after_reading = false
    }
  }
  sink "file" {
    config = {
      path = "/vault/secrets/.vault-token"
    }
  }
}

template {
  source      = "/vault/agent-config/credentials.env.tmpl"
  destination = "/vault/secrets/credentials.env"
  perms       = "0444"
}

exit_after_auth = true
```

This file is generally identical across services — only the
`<service>` directory name differs. The `vault.address` is the
container DNS name `vault-server:8200`, NOT a `*.internal` URL
(D-17-38 Finding 6: `*.internal` resolution does not work from
inside the Docker network).

### 4.2 `credentials.env.tmpl`

Verbatim from `docker/vault-agent-buildarr/credentials.env.tmpl`
(lines 1–13, file is 13 lines):

```
{{ with secret "secret/data/arr/radarr" -}}
RADARR_API_KEY={{ .Data.data.api_key }}
{{- end }}
{{ with secret "secret/data/arr/prowlarr" -}}
PROWLARR_API_KEY={{ .Data.data.api_key }}
{{- end }}
{{ with secret "secret/data/arr/sonarr" -}}
SONARR_API_KEY={{ .Data.data.api_key }}
{{- end }}
{{ with secret "secret/data/arr/sportarr" -}}
SPORTARR_API_KEY={{ .Data.data.api_key }}
{{- end }}
```

One `{{ with secret "..." -}}` block per Vault path the policy
grants. Path form `secret/data/<domain>/<name>` matches the policy
exactly. Field reference `.Data.data.<field>` is KV v2 shape.

The blocks in this template MUST mirror the paths in
`config/vault-policies/<service>-policy.hcl` 1:1. A block referencing
a path the policy does not grant will fail at render time with a
permission-denied error from Vault Agent.

## 5. Author the provision script

Path convention: `scripts/provision-<service>.sh`. Header doctrine
fields, verbatim from `provision-buildarr.sh` (lines 2–10):

```bash
# D-17-44 — provision Vault policy and AppRole for Buildarr config-as-code substrate.
#
# Idempotent: safe to re-run. No secrets generated here — Buildarr reads
# existing secret/arr/{radarr,prowlarr,sonarr,sportarr} paths provisioned by D-17-38.
#
# Doctrine: hash-only verification, no value display. D-17-38 credential pattern.
# Run from repo root on Mac Mini.

set -euo pipefail
```

Standard initialisation (lines 12–18):

```bash
DOCKER=/opt/homebrew/bin/docker
source "$(dirname "$0")/lib/vault-admin-token.sh"
VAULT_TOKEN=$(resolve_admin_vault_token) || exit 2
SERVICE=buildarr
APPROLE_DIR="/Users/admin/.vault-approle/${SERVICE}"
SECRETS_DIR="/Users/admin/.vault-agent-secrets/${SERVICE}"
POLICY_FILE="config/vault-policies/${SERVICE}-policy.hcl"
```

Section layout (taken from the buildarr script's explicit `Step N`
banners, lines 27 / 33 / 42 / 67 / 73):

1. **Step 1 — write policy** (`docker cp` + `vault policy write`).
2. **Step 2 — create AppRole** (`vault write auth/approle/role/...`).
3. **Step 3 — capture role-id + secret-id** (idempotent file checks).
4. **Step 4 — secrets directory** (`mkdir -p ${SECRETS_DIR}; chmod 0700`).
5. **Step 5 — verify AppRole can read** (hash-only smoke test).

Sibling provision scripts (bazarr, scraparr, cleanuparr) follow the
same overall flow but vary section count and include extra logic
(scraparr ships a `sha12` helper; cleanuparr is more compact). Use
the buildarr 5-step layout as the canonical template; deviate only
when service-specific logic warrants it.

## 6. Verify (hash-only)

The verification step authenticates with role-id + secret-id, then
reads each granted path and emits a fingerprint of the value —
never the value itself.

**Hash-algo note (real divergence between sources):**

- The pattern doc `vault-agent-sidecar-pattern.md` (line 287) uses
  `sha256[:12]`:
  ```bash
  vault kv get -field=api_key secret/arr/sonarr | sha256sum | cut -c1-12
  ```
- Sibling scripts `provision-bazarr.sh`, `provision-scraparr.sh`,
  `provision-cleanuparr.sh` all use `sha256[:12]` (e.g. bazarr
  line 81: `print(hashlib.sha256(v.encode()).hexdigest()[:12])`).
- `provision-buildarr.sh` (line 91) uses `md5[:12]`:
  ```python
  print(hashlib.md5(v.encode()).hexdigest()[:12])
  ```
  This is a real outlier — buildarr predates the post-D-17-38
  hash-doctrine harmonisation. **For new services, use `sha256[:12]`.**
  The buildarr divergence should be normalised when the script is
  next touched.

Canonical sha256 verification block, verbatim from
`provision-bazarr.sh` (lines 75–83 with surrounding context):

```bash
HASH=$(echo "$RESULT" | python3 -c "
import sys, json, hashlib
d=json.load(sys.stdin)
v=d['data']['data']['api_key']
print(hashlib.sha256(v.encode()).hexdigest()[:12])
")
log "  ${path}#api_key: readable; sha256[12]: ${HASH}"
```

Equal fingerprint across substrates = same credential. Unequal =
drift. Values themselves never leave the host they live on.

## Failure modes

1. **Admin token cannot be resolved.** The provision script exits
   2 at line 14 (`VAULT_TOKEN=$(resolve_admin_vault_token) || exit 2`).
   The helper logs which sources it tried (lines 106–108):
   ```
   ERROR: could not resolve a valid Vault admin token from any source
     tried: $VAULT_TOKEN env, ~/vault-init-keys-NEW-*.txt (newest), ~/.vault-token
     ensure ~/vault-init-keys-NEW-*.txt exists with 'Initial Root Token: hvs.XXX' line
   ```
   Fix: ensure the post-rebuild keys file is present at
   `~/vault-init-keys-NEW-*.txt` and contains `Initial Root Token:
   hvs.XXX`.

2. **Policy file not found.** The provision script exits 1 at line
   24 with `ERROR: policy file ${POLICY_FILE} not found (run from
   repo root)`. Fix: run from the repo root, not from
   `scripts/`.

3. **AppRole already exists.** `vault write auth/approle/role/...`
   is upsert — running it on an existing AppRole overwrites the
   role's parameters but does NOT mint a new secret-id. The script's
   step-3 idempotency guard prevents re-minting; to rotate
   credentials, delete `~/.vault-approle/<service>/secret-id` first.

4. **Policy syntax error.** `vault policy write` rejects invalid
   HCL with a non-zero exit; `set -euo pipefail` aborts the script
   at step 1.

5. **Sidecar template render failure.** Vault Agent fails at startup
   if a `{{ with secret "..." }}` block references a path the policy
   does not grant — render error surfaces as a permission-denied
   line in the agent container's logs. Fix: ensure
   `credentials.env.tmpl` paths and `<service>-policy.hcl` paths
   match 1:1.

6. **Verification step fails.** If a `secret/<domain>/<name>` path
   doesn't exist or doesn't have an `api_key` field, the smoke-test
   loop exits 1 with `ERROR: ${path} not readable or missing api_key`
   (provision-buildarr.sh line 96). The AppRole + sidecar will work
   for the paths that do exist; fix by either creating the missing
   secret or removing the path from the policy + template.

## Rotation + retirement

To rotate the secret-id:

```bash
rm ~/.vault-approle/<service>/secret-id
./scripts/provision-<service>.sh
```

(role-id is stable; only secret-id is bootstrap material that
should rotate.)

To retire the AppRole when the service is decommissioned, follow
[`retire-service.md`](retire-service.md) (D-17-57) for the full
disposition flow — Vault path, sidecar artifacts, secrets-dir,
and framework state must converge before the retirement is
considered complete.

## Cross-references

- [`vault-agent-sidecar-pattern.md`](../architecture-facts/vault-agent-sidecar-pattern.md) —
  architecture-fact carrying the *why* of the sidecar pattern, the
  KV v2 path conventions, and the hash-only verification doctrine.
- [`retire-service.md`](retire-service.md) — D-17-57 retirement
  flow; AppRole + secret-id + policy disposition is one of the
  authority surfaces that must converge.
- `scripts/provision-buildarr.sh` — canonical reference
  implementation for this pattern.
