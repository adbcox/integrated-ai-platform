#!/bin/sh
set -eu

BASE_DIR="${BASE_DIR:-$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)}"
BASE_URL="${BASE_URL:-http://127.0.0.1:8010}"
ENV_FILE="${ENV_FILE:-$BASE_DIR/.env}"

if ! command -v curl >/dev/null 2>&1; then
  echo "Missing required command: curl"
  exit 1
fi

TOKEN="${API_TOKEN:-}"
if [ -z "$TOKEN" ]; then
  if [ ! -f "$ENV_FILE" ]; then
    echo "Missing env file: $ENV_FILE"
    exit 1
  fi
  TOKEN="$(grep '^API_TOKEN=' "$ENV_FILE" | cut -d= -f2- || true)"
fi
if [ -z "$TOKEN" ]; then
  echo "API_TOKEN missing (set API_TOKEN env var or define it in $ENV_FILE)"
  exit 1
fi

api_post() {
  endpoint="$1"
  body="$2"
  curl -s -X POST "$BASE_URL$endpoint" \
    -H "Content-Type: application/json" \
    -H "X-API-Token: $TOKEN" \
    -d "$body"
}

cmd="${1:-}"
shift || true

case "$cmd" in
  health)
    curl -s "$BASE_URL/health"
    ;;

  start)
    curl -s -X POST "$BASE_URL/session/start" \
      -H "X-API-Token: $TOKEN"
    ;;

  close)
    SESSION_ID="${1:?session_id required}"
    api_post "/session/close" "{\"session_id\":\"$SESSION_ID\"}"
    ;;

  open)
    SESSION_ID="${1:?session_id required}"
    URL="${2:?url required}"
    api_post "/session/open" "{\"session_id\":\"$SESSION_ID\",\"url\":\"$URL\"}"
    ;;

  read)
    SESSION_ID="${1:?session_id required}"
    api_post "/session/read" "{\"session_id\":\"$SESSION_ID\"}"
    ;;

  click-text)
    SESSION_ID="${1:?session_id required}"
    TEXT="${2:?text required}"
    api_post "/session/click" "{\"session_id\":\"$SESSION_ID\",\"text\":\"$TEXT\"}"
    ;;

  click-js-text)
    SESSION_ID="${1:?session_id required}"
    TEXT="${2:?text required}"
    api_post "/session/click" "{\"session_id\":\"$SESSION_ID\",\"text\":\"$TEXT\"}"
    ;;

  click-selector)
    SESSION_ID="${1:?session_id required}"
    SELECTOR="${2:?selector required}"
    api_post "/session/click" "{\"session_id\":\"$SESSION_ID\",\"selector\":\"$SELECTOR\"}"
    ;;

  click-index)
    SESSION_ID="${1:?session_id required}"
    INDEX="${2:?index required}"
    api_post "/session/click" "{\"session_id\":\"$SESSION_ID\",\"index\":$INDEX}"
    ;;

  type)
    SESSION_ID="${1:?session_id required}"
    SELECTOR="${2:?selector required}"
    TEXT="${3:?text required}"
    api_post "/session/type" "{\"session_id\":\"$SESSION_ID\",\"selector\":\"$SELECTOR\",\"text\":\"$TEXT\"}"
    ;;

  fill-input-index)
    SESSION_ID="${1:?session_id required}"
    INDEX="${2:?index required}"
    TEXT="${3:?text required}"
    SELECTOR="input >> nth=$INDEX"
    api_post "/session/type" "{\"session_id\":\"$SESSION_ID\",\"selector\":\"$SELECTOR\",\"text\":\"$TEXT\"}"
    ;;

  press)
    SESSION_ID="${1:?session_id required}"
    KEY="${2:?key required}"
    api_post "/session/press" "{\"session_id\":\"$SESSION_ID\",\"key\":\"$KEY\"}"
    ;;

  wait)
    SESSION_ID="${1:?session_id required}"
    MS="${2:?ms required}"
    api_post "/session/wait" "{\"session_id\":\"$SESSION_ID\",\"ms\":$MS}"
    ;;

  screenshot)
    SESSION_ID="${1:?session_id required}"
    NAME="${2:-shot.png}"
    api_post "/session/screenshot" "{\"session_id\":\"$SESSION_ID\",\"name\":\"$NAME\"}"
    ;;

  list)
    SESSION_ID="${1:?session_id required}"
    api_post "/session/list-clickable" "{\"session_id\":\"$SESSION_ID\"}"
    ;;

  list-clickable)
    SESSION_ID="${1:?session_id required}"
    api_post "/session/list-clickable" "{\"session_id\":\"$SESSION_ID\"}"
    ;;

  list-inputs)
    SESSION_ID="${1:?session_id required}"
    printf '{"session_id":"%s","note":"list-inputs compatibility shim active; fill-input-index uses selector input >> nth=N","items":[]}\n' "$SESSION_ID"
    ;;

  dom-snapshot)
    SESSION_ID="${1:?session_id required}"
    api_post "/session/read" "{\"session_id\":\"$SESSION_ID\"}"
    ;;

  *)
    echo "Usage:"
    echo "  bop health"
    echo "  bop start"
    echo "  bop close <session_id>"
    echo "  bop open <session_id> <url>"
    echo "  bop read <session_id>"
    echo "  bop click-text <session_id> <text>"
    echo "  bop click-js-text <session_id> <text>"
    echo "  bop click-selector <session_id> <selector>"
    echo "  bop click-index <session_id> <index>"
    echo "  bop type <session_id> <selector> <text>"
    echo "  bop fill-input-index <session_id> <index> <text>"
    echo "  bop press <session_id> <key>"
    echo "  bop wait <session_id> <ms>"
    echo "  bop screenshot <session_id> [name]"
    echo "  bop list <session_id>"
    echo "  bop list-clickable <session_id>"
    echo "  bop list-inputs <session_id>"
    echo "  bop dom-snapshot <session_id>"
    exit 1
    ;;
esac

echo ""
