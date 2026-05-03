#!/usr/bin/env bash
# D-17-13 — Goose launcher with platform-litellm provider injection.
#
# Reads the litellm master key from Vault (secret/litellm/master#master_key)
# and exports it as OPENAI_API_KEY for Goose's openai provider, which is
# pointed at the platform litellm-gateway (host port 4000) via OPENAI_HOST.
#
# Vault root token is read from ~/vault-init-keys-NEW-20260430.txt
# (operator-only file, mode 600). The Goose process never sees the root
# token — only the litellm bearer key, which it needs by API contract.
#
# Usage:
#   scripts/goose/goose-platform.sh                # interactive session
#   scripts/goose/goose-platform.sh session        # explicit session
#   scripts/goose/goose-platform.sh run -i task.md # run an instruction file
#
# All arguments are passed verbatim to the goose CLI.
set -euo pipefail

VAULT_KEYFILE="${VAULT_KEYFILE:-$HOME/vault-init-keys-NEW-20260430.txt}"
LITELLM_HOST="${LITELLM_HOST:-http://127.0.0.1:4000}"

if [[ ! -r "$VAULT_KEYFILE" ]]; then
  echo "ERROR: vault key file not readable: $VAULT_KEYFILE" >&2
  echo "       set VAULT_KEYFILE if it lives elsewhere." >&2
  exit 2
fi

ROOT_TOKEN="$(grep '^Initial Root Token:' "$VAULT_KEYFILE" | awk '{print $NF}')"
if [[ -z "${ROOT_TOKEN}" ]]; then
  echo "ERROR: could not parse root token from $VAULT_KEYFILE" >&2
  exit 2
fi

# Pull the litellm master key. Stored at secret/litellm/master#master_key.
# We read the value into a local var; never echoed.
MASTER_KEY="$(
  docker exec -e VAULT_TOKEN="$ROOT_TOKEN" vault-server \
    vault kv get -field=master_key secret/litellm/master 2>/dev/null
)"
if [[ -z "${MASTER_KEY}" ]]; then
  echo "ERROR: could not fetch secret/litellm/master#master_key from Vault" >&2
  echo "       (vault-server container down? see docs/runbooks/vault-unseal.md)" >&2
  exit 3
fi

# Hash-only confirmation that the key looks right (operator can compare to
# D-17-26 chronicle which records SHA-256[:12] = 439bcdb691d6).
KEY_FP="$(printf '%s' "$MASTER_KEY" | shasum -a 256 | cut -c1-12)"
echo "[goose-platform] litellm key sha256[:12]=$KEY_FP host=$LITELLM_HOST" >&2

export OPENAI_API_KEY="$MASTER_KEY"
export OPENAI_HOST="$LITELLM_HOST"

# Drop ROOT_TOKEN from the env handed to goose.
unset ROOT_TOKEN MASTER_KEY VAULT_KEYFILE

exec goose "$@"
