#!/usr/bin/env bash
# deploy-stack.sh — generate .env from Vault then bring up a Docker Compose stack
#
# Usage:
#   export VAULT_TOKEN=<token>
#   ./scripts/deploy-stack.sh <stack-dir>
#
# Example:
#   ./scripts/deploy-stack.sh docker/plane
#
# The stack directory must contain a vault-mapping.yaml.
# The script will:
#   1. Read vault-mapping.yaml
#   2. Pull each secret from Vault via docker exec
#   3. Write a .env file in the stack directory
#   4. Run docker compose up -d

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/vault-env.sh"

STACK_DIR="${1:-}"
if [[ -z "$STACK_DIR" ]]; then
    echo "Usage: $0 <stack-dir>" >&2
    exit 1
fi

if [[ ! -d "$STACK_DIR" ]]; then
    echo "ERROR: Stack directory not found: $STACK_DIR" >&2
    exit 1
fi

MAPPING="$STACK_DIR/vault-mapping.yaml"
if [[ ! -f "$MAPPING" ]]; then
    echo "ERROR: No vault-mapping.yaml in $STACK_DIR" >&2
    echo "Create one with lines like: ENV_VAR_NAME: secret/path:field" >&2
    exit 1
fi

if [[ -z "${VAULT_TOKEN:-}" ]]; then
    echo "ERROR: VAULT_TOKEN not set." >&2
    exit 1
fi

ENV_FILE="$STACK_DIR/.env"
BACKUP=""
if [[ -f "$ENV_FILE" ]]; then
    BACKUP="${ENV_FILE}.bak.$(date +%Y%m%d-%H%M%S)"
    cp "$ENV_FILE" "$BACKUP"
    echo "Backed up existing .env to $BACKUP"
fi

echo "Generating $ENV_FILE from $MAPPING ..."
generate_env_from_mapping "$MAPPING" "$ENV_FILE"

echo "Generated $(wc -l < "$ENV_FILE") lines"

echo "Bringing up stack in $STACK_DIR ..."
docker compose -f "$STACK_DIR/docker-compose.yml" up -d

echo "Done."
