#!/usr/bin/env bash
# vault-env.sh — helpers for reading secrets from Vault via docker exec
# Source this file: source scripts/lib/vault-env.sh

set -euo pipefail

VAULT_CONTAINER="${VAULT_CONTAINER:-vault-server}"

_require_vault_token() {
    if [[ -z "${VAULT_TOKEN:-}" ]]; then
        echo "ERROR: VAULT_TOKEN not set. Export it before sourcing vault-env.sh" >&2
        return 1
    fi
}

# vault_get <path> <field>
# e.g. vault_get secret/plex/api token
vault_get() {
    local path="$1" field="$2"
    _require_vault_token
    docker exec -e VAULT_TOKEN="$VAULT_TOKEN" "$VAULT_CONTAINER" \
        vault kv get -field="$field" "$path" 2>/dev/null
}

# vault_put <path> key=value [key=value ...]
vault_put() {
    local path="$1"; shift
    _require_vault_token
    docker exec -e VAULT_TOKEN="$VAULT_TOKEN" "$VAULT_CONTAINER" \
        vault kv put "$path" "$@"
}

# generate_env_from_mapping <mapping_file> [output_file]
# Reads a vault-mapping.yaml and writes a .env file.
# If output_file is omitted, prints to stdout.
generate_env_from_mapping() {
    local mapping_file="$1"
    local output_file="${2:-}"
    _require_vault_token

    local script_dir
    script_dir="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" 2>/dev/null && pwd)"
    local gen_script="$script_dir/vault-generate-env.py"

    if [[ -n "$output_file" ]]; then
        python3 "$gen_script" "$mapping_file" "$VAULT_TOKEN" "${VAULT_CONTAINER:-vault-server}" "$output_file"
    else
        python3 "$gen_script" "$mapping_file" "$VAULT_TOKEN" "${VAULT_CONTAINER:-vault-server}"
    fi
}
