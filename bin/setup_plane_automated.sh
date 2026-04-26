#!/usr/bin/env bash
# setup_plane_automated.sh — zero-manual-steps Plane CE setup
#
# Usage:
#   bash bin/setup_plane_automated.sh                  # full setup + sync
#   bash bin/setup_plane_automated.sh --dry-run        # no writes
#   bash bin/setup_plane_automated.sh --skip-sync      # skip 600-item sync
#   bash bin/setup_plane_automated.sh --skip-instance  # instance already configured
#
# Expects:
#   - Plane CE containers running (docker compose -f docker/docker-compose-plane.yml up -d)
#   - docker/.env with PLANE_ADMIN_EMAIL and PLANE_ADMIN_PASSWORD set
#   - Python 3.9+ in PATH
#
# On completion, prints login URL, credentials, and MCP registration command.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCRIPT="$REPO_ROOT/bin/setup_plane_automated.py"

# ── Argument forwarding ───────────────────────────────────────────────────────
FORWARD_ARGS=()
for arg in "$@"; do
    case "$arg" in
        --dry-run)        FORWARD_ARGS+=(--dry-run) ;;
        --skip-sync)      FORWARD_ARGS+=(--skip-sync) ;;
        --skip-instance)  FORWARD_ARGS+=(--skip-instance-setup) ;;
        --url=*)          FORWARD_ARGS+=("$arg") ;;
        --email=*)        FORWARD_ARGS+=("$arg") ;;
        --password=*)     FORWARD_ARGS+=("$arg") ;;
        --workspace=*)    FORWARD_ARGS+=("$arg") ;;
        -h|--help)
            echo "Usage: $0 [--dry-run] [--skip-sync] [--skip-instance] [--url=URL] [--email=EMAIL] [--password=PWD]"
            exit 0 ;;
        *)
            echo "Unknown option: $arg" >&2; exit 1 ;;
    esac
done

# ── Pre-flight checks ─────────────────────────────────────────────────────────
echo "=== Plane CE Automated Setup ==="
echo ""

# Python check
if ! command -v python3 &>/dev/null; then
    echo "ERROR: python3 not found in PATH" >&2
    exit 1
fi

# Docker check
if ! command -v docker &>/dev/null; then
    echo "ERROR: docker not found in PATH" >&2
    exit 1
fi

# Check plane-api container is running
if ! docker ps --format '{{.Names}}' 2>/dev/null | grep -q "plane-api"; then
    echo "ERROR: plane-api container not running."
    echo "  Start with: docker compose -f docker/docker-compose-plane.yml up -d"
    exit 1
fi

# .env check
ENV_FILE="$REPO_ROOT/docker/.env"
if [[ ! -f "$ENV_FILE" ]]; then
    echo "ERROR: $ENV_FILE not found"
    echo "  Copy from: cp docker/.env.example docker/.env"
    exit 1
fi

# Password check
if ! grep -q "PLANE_ADMIN_PASSWORD=" "$ENV_FILE" || \
   [[ "$(grep "PLANE_ADMIN_PASSWORD=" "$ENV_FILE" | cut -d= -f2)" == "" ]]; then
    echo "ERROR: PLANE_ADMIN_PASSWORD not set in docker/.env"
    exit 1
fi

echo "  Plane API container: running"
echo "  Config:             $ENV_FILE"
echo ""

# ── Run the Python setup script ───────────────────────────────────────────────
exec python3 "$SCRIPT" "${FORWARD_ARGS[@]}"
