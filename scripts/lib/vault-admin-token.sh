#!/usr/bin/env bash
# vault-admin-token.sh — resolve a Vault admin (root-equivalent) token for
# provision-*.sh scripts that need to create policies, AppRoles, and
# secrets paths.
#
# Source this file from a provision script:
#     source "$(dirname "$0")/lib/vault-admin-token.sh"
#     VAULT_TOKEN=$(resolve_admin_vault_token)
#
# Lookup precedence:
#   1. ${VAULT_TOKEN} already exported (CI / operator override)
#   2. Newest ~/vault-init-keys-NEW-*.txt (post-rebuild canonical keys file,
#      mtime-sorted to survive future rebuilds without code change)
#   3. ${HOME}/.vault-token IFF it validates against the live Vault
#      (kept ONLY for backwards-compat; will be skipped silently if stale)
#
# Fails loudly if no source resolves a valid admin token. Never falls
# back to a token that doesn't validate. Never echoes token values.
#
# Doctrine alignment:
#   - Root-token use is acceptable for one-shot admin work like policy
#     creation (see CLAUDE.md "Vault Operations").
#   - Per-service runtime auth uses AppRoles minted BY this script, not
#     this token.
#   - Hash-only output: emits source name + "ok", never the token.

_vat_log() { printf '[vault-admin-token] %s\n' "$*" >&2; }

_vat_validate_token() {
    # Validate token via docker exec → vault token lookup. Quiet on
    # success, returns non-zero on failure. Suppresses all token-bearing
    # output.
    local token="$1"
    /opt/homebrew/bin/docker exec -e VAULT_TOKEN="$token" vault-server \
        vault token lookup >/dev/null 2>&1
}

_vat_newest_init_keys_file() {
    # Echo path to newest ~/vault-init-keys-NEW-*.txt (mtime order),
    # or empty if none exist. Globs (not hardcoded date) so future
    # post-loss rebuilds work without editing this helper.
    /bin/ls -t "${HOME}"/vault-init-keys-NEW-*.txt 2>/dev/null | /usr/bin/head -n 1
}

_vat_read_root_token_from_file() {
    # Extract "Initial Root Token: hvs.XXX" value from the given file.
    local file="$1"
    /usr/bin/awk -F': ' '/Initial Root Token/{print $2; exit}' "$file"
}

resolve_admin_vault_token() {
    local token=""
    local source=""

    # 1. Explicit env override
    if [ -n "${VAULT_TOKEN:-}" ]; then
        if _vat_validate_token "$VAULT_TOKEN"; then
            _vat_log "using VAULT_TOKEN from environment (validated)"
            printf '%s' "$VAULT_TOKEN"
            return 0
        else
            _vat_log "VAULT_TOKEN env var present but invalid; trying other sources"
        fi
    fi

    # 2. Newest vault-init-keys-NEW-*.txt
    local keys_file
    keys_file=$(_vat_newest_init_keys_file)
    if [ -n "$keys_file" ] && [ -r "$keys_file" ]; then
        token=$(_vat_read_root_token_from_file "$keys_file")
        if [ -n "$token" ] && _vat_validate_token "$token"; then
            _vat_log "loaded admin token from ${keys_file} (validated)"
            printf '%s' "$token"
            unset token
            return 0
        fi
    fi

    # 3. ~/.vault-token (legacy) — accept ONLY if it validates
    if [ -r "${HOME}/.vault-token" ]; then
        token=$(/bin/cat "${HOME}/.vault-token")
        if [ -n "$token" ] && _vat_validate_token "$token"; then
            _vat_log "loaded admin token from ~/.vault-token (validated; consider migrating to vault-init-keys-NEW-*.txt)"
            printf '%s' "$token"
            unset token
            return 0
        fi
        _vat_log "~/.vault-token present but stale/invalid (likely pre-rebuild); skipping"
    fi

    _vat_log "ERROR: could not resolve a valid Vault admin token from any source"
    _vat_log "  tried: \$VAULT_TOKEN env, ~/vault-init-keys-NEW-*.txt (newest), ~/.vault-token"
    _vat_log "  ensure ~/vault-init-keys-NEW-*.txt exists with 'Initial Root Token: hvs.XXX' line"
    return 1
}
