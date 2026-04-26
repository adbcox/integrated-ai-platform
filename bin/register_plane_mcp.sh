#!/usr/bin/env bash
# Print (and optionally run) the claude mcp add command for plane-roadmap.
# Reads credentials from docker/.env — run setup_plane_automated.py first.
#
# Usage:
#   bash bin/register_plane_mcp.sh          # print command only
#   bash bin/register_plane_mcp.sh --apply  # actually run claude mcp add

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ENV_FILE="$REPO_ROOT/docker/.env"

# ── Read docker/.env ──────────────────────────────────────────────────────────
_env() {
    local key="$1" default="${2:-}"
    local val
    val=$(grep -E "^${key}=" "$ENV_FILE" 2>/dev/null | tail -1 | cut -d= -f2- | tr -d '\r') || true
    echo "${val:-$default}"
}

if [[ ! -f "$ENV_FILE" ]]; then
    echo "ERROR: $ENV_FILE not found. Run setup_plane_automated.py first." >&2
    exit 1
fi

PLANE_URL=$(_env PLANE_URL "http://localhost:8000")
PLANE_API_TOKEN=$(_env PLANE_API_TOKEN "")
PLANE_WORKSPACE=$(_env PLANE_WORKSPACE "iap")
PLANE_PROJECT_ID=$(_env PLANE_PROJECT_ID "")
MCP_SCRIPT="$REPO_ROOT/mcp/plane_mcp_server.py"

# ── Validate ──────────────────────────────────────────────────────────────────
if [[ -z "$PLANE_API_TOKEN" ]]; then
    echo "ERROR: PLANE_API_TOKEN is empty in $ENV_FILE"
    echo "  Run: python3 bin/setup_plane_automated.py"
    exit 1
fi

if [[ -z "$PLANE_PROJECT_ID" ]]; then
    echo "ERROR: PLANE_PROJECT_ID is empty in $ENV_FILE"
    echo "  Run: python3 bin/setup_plane_automated.py"
    exit 1
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  MCP server: plane-roadmap"
echo "  Script:     $MCP_SCRIPT"
echo "  URL:        $PLANE_URL"
echo "  Workspace:  $PLANE_WORKSPACE"
echo "  Project:    $PLANE_PROJECT_ID"
echo "  Token:      ${PLANE_API_TOKEN:0:8}…"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Command to register:"
echo ""
echo "  claude mcp add plane-roadmap \\"
echo "    -e \"PLANE_URL=$PLANE_URL\" \\"
echo "    -e \"PLANE_API_TOKEN=$PLANE_API_TOKEN\" \\"
echo "    -e \"PLANE_WORKSPACE=$PLANE_WORKSPACE\" \\"
echo "    -e \"PLANE_PROJECT_ID=$PLANE_PROJECT_ID\" \\"
echo "    -- python3 \"$MCP_SCRIPT\""
echo ""

if [[ "${1:-}" == "--apply" ]]; then
    echo "Running: claude mcp add …"
    claude mcp add plane-roadmap \
        -e "PLANE_URL=$PLANE_URL" \
        -e "PLANE_API_TOKEN=$PLANE_API_TOKEN" \
        -e "PLANE_WORKSPACE=$PLANE_WORKSPACE" \
        -e "PLANE_PROJECT_ID=$PLANE_PROJECT_ID" \
        -- python3 "$MCP_SCRIPT"
    echo ""
    echo "Registered. Verify with:  claude mcp list"
else
    echo "  (pass --apply to run the command automatically)"
fi
