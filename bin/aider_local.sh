#!/usr/bin/env bash
set -euo pipefail

BASE_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
# Live local Ollama default: 127.0.0.1:11434 (verified by /api/tags).
API_BASE="http://127.0.0.1:11434"
MODEL="ollama_chat/qwen2.5-coder:14b"
MAP_TOKENS="1024"
TIMEOUT="180"
MODE_LABEL="local"
HAS_MODEL_OVERRIDE=0
HAS_MAP_TOKENS_OVERRIDE=0
HAS_TIMEOUT_OVERRIDE=0
HAS_API_BASE_OVERRIDE=0
MICRO_MODEL="${MICRO_MODEL:-ollama_chat/local-micro-coder-fast}"
MICRO_MAP_TOKENS="${MICRO_MAP_TOKENS:-0}"
MICRO_TIMEOUT="${MICRO_TIMEOUT:-45}"
SMART_STATUS_ONLY=0
USER_MODEL=""
USER_MAP_TOKENS=""
USER_TIMEOUT=""

PASSTHRU_ARGS=()

append_passthru() {
  PASSTHRU_ARGS+=("$1")
}

usage() {
  cat <<'USAGE'
Usage:
  ./bin/aider_local.sh [--hard] [--smart] [--gpu-experimental] [--api-base <url>] [--smart-status] [aider args...]

Default fast lane settings:
  OLLAMA_API_BASE defaults to http://127.0.0.1:11434
  --model ollama_chat/qwen2.5-coder:14b
  --map-tokens 1024
  --timeout 180

Options:
  --hard               Use explicit harder-task profile (deepseek-coder-v2, map-tokens 2048, timeout 240)
  --micro-profile      Opt into local-micro-coder-fast profile (Stage 3 experiments)
  --smart              Use 32B smart profile (requires OLLAMA_API_BASE_32B or --api-base)
  --gpu-experimental   Alias for the default endpoint (127.0.0.1:11434).
  --api-base <url>     Override Ollama API base URL
  --smart-status       Check the configured smart (32B) endpoint and exit
  -h, --help           Show help
USAGE
}

smart_status() {
  local base="$1"
  local ping="${base%/}/api/tags"
  echo "[aider-local] smart-status: checking $base"
  if curl -sS --max-time 5 --connect-timeout 2 "$ping" >/dev/null; then
    echo "[aider-local] smart-status: OK"
    exit 0
  fi
  echo "ERROR: smart endpoint '$base' is unreachable. Ensure OLLAMA_API_BASE_32B or --api-base points to the live 32B server." >&2
  exit 1
}

ping_ollama_or_fail_once() {
  local base="$1"
  local mode_label="$2"
  local ping="${base%/}/api/tags"
  local tmp_log="/tmp/aider_local_ping.$$"
  local http_code
  http_code=$(curl -sS -o /dev/null -w "%{http_code}" --max-time 4 --connect-timeout 2 "$ping" 2>"$tmp_log" || echo "curl_error")
  if [ "$http_code" = "200" ]; then
    rm -f "$tmp_log"
    return 0
  fi
  echo "[aider-local] ping failed for mode '$mode_label' at $base" >&2
  local details
  details="$(cat "$tmp_log" 2>/dev/null || true)"
  rm -f "$tmp_log"
  if [ "$http_code" = "curl_error" ]; then
    echo "ERROR[$mode_label]: Ollama endpoint '$base' unreachable ($details)" >&2
  else
    echo "ERROR[$mode_label]: Ollama endpoint '$base' responded with HTTP $http_code ($details)" >&2
  fi
  local port
  port=$(printf '%s' "$base" | awk -F: '{print $3}')
  echo "hint: ensure 'ollama serve' (port ${port:-unknown}) is running or set OLLAMA_API_BASE" >&2
  echo "hint: skip this check with AIDER_LOCAL_SKIP_PING=1 if you already manage connectivity" >&2
  return 1
}

ping_ollama_with_retry() {
  local base="$1"
  local mode_label="$2"
  local attempts="${AIDER_LOCAL_PING_RETRIES:-3}"
  local delay="${AIDER_LOCAL_PING_DELAY:-2}"
  local i=1
  while [ "$i" -le "$attempts" ]; do
    if ping_ollama_or_fail_once "$base" "$mode_label"; then
      return 0
    fi
    if [ "$i" -lt "$attempts" ]; then
      echo "[aider-local] ping attempt $i failed; retrying in ${delay}s" >&2
      sleep "$delay"
    fi
    i=$((i + 1))
  done
  ping_ollama_or_fail_once "$base" "$mode_label"
}

ping_ollama_or_fail() {
  local base="$1"
  local mode_label="$2"
  ping_ollama_with_retry "$base" "$mode_label"
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --hard)
      MODEL="ollama_chat/deepseek-coder-v2:latest"
      MAP_TOKENS="2048"
      TIMEOUT="240"
      MODE_LABEL="hard"
      shift
      ;;
    --micro-profile)
      MODEL="$MICRO_MODEL"
      MAP_TOKENS="$MICRO_MAP_TOKENS"
      TIMEOUT="$MICRO_TIMEOUT"
      MODE_LABEL="micro-opt"
      HAS_MODEL_OVERRIDE=1
      HAS_MAP_TOKENS_OVERRIDE=1
      HAS_TIMEOUT_OVERRIDE=1
      shift
      ;;
    --smart)
      MODE_LABEL="smart"
      MODEL="ollama_chat/qwen2.5-coder:32b"
      MAP_TOKENS="4096"
      TIMEOUT="240"
      if [ "$HAS_API_BASE_OVERRIDE" -eq 0 ]; then
        if [ -n "${OLLAMA_API_BASE_32B:-}" ]; then
          API_BASE="$OLLAMA_API_BASE_32B"
        else
          echo "ERROR: --smart requires OLLAMA_API_BASE_32B or --api-base" >&2
          exit 1
        fi
      fi
      shift
      ;;
    --gpu-experimental)
      API_BASE="http://127.0.0.1:11434"
      HAS_API_BASE_OVERRIDE=1
      shift
      ;;
    --api-base)
      API_BASE="${2:-}"
      [ -n "$API_BASE" ] || { echo "ERROR: --api-base requires a value" >&2; exit 1; }
      HAS_API_BASE_OVERRIDE=1
      shift 2
      ;;
    --smart-status)
      SMART_STATUS_ONLY=1
      shift
      ;;
    --)
      shift
      while [ "$#" -gt 0 ]; do
        append_passthru "$1"
        shift
      done
      break
      ;;
    --model)
      [ "$#" -ge 2 ] || { echo "ERROR: --model requires a value" >&2; exit 1; }
      HAS_MODEL_OVERRIDE=1
      USER_MODEL="$2"
      append_passthru "$1"
      append_passthru "$2"
      shift 2
      ;;
    --model=*)
      HAS_MODEL_OVERRIDE=1
      USER_MODEL="${1#--model=}"
      append_passthru "$1"
      shift
      ;;
    --map-tokens)
      [ "$#" -ge 2 ] || { echo "ERROR: --map-tokens requires a value" >&2; exit 1; }
      HAS_MAP_TOKENS_OVERRIDE=1
      USER_MAP_TOKENS="$2"
      append_passthru "$1"
      append_passthru "$2"
      shift 2
      ;;
    --map-tokens=*)
      HAS_MAP_TOKENS_OVERRIDE=1
      USER_MAP_TOKENS="${1#--map-tokens=}"
      append_passthru "$1"
      shift
      ;;
    --timeout)
      [ "$#" -ge 2 ] || { echo "ERROR: --timeout requires a value" >&2; exit 1; }
      HAS_TIMEOUT_OVERRIDE=1
      USER_TIMEOUT="$2"
      append_passthru "$1"
      append_passthru "$2"
      shift 2
      ;;
    --timeout=*)
      HAS_TIMEOUT_OVERRIDE=1
      USER_TIMEOUT="${1#--timeout=}"
      append_passthru "$1"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      append_passthru "$1"
      shift
      ;;
  esac
done

if [ "$SMART_STATUS_ONLY" -eq 1 ]; then
  SMART_BASE=""
  if [ "$HAS_API_BASE_OVERRIDE" -eq 1 ]; then
    SMART_BASE="$API_BASE"
  elif [ -n "${OLLAMA_API_BASE_32B:-}" ]; then
    SMART_BASE="$OLLAMA_API_BASE_32B"
  else
    echo "ERROR: --smart-status requires OLLAMA_API_BASE_32B or --api-base" >&2
    exit 1
  fi
  smart_status "$SMART_BASE"
fi

export OLLAMA_API_BASE="$API_BASE"

if [ "${AIDER_LOCAL_SKIP_PING:-0}" != "1" ]; then
  ping_ollama_or_fail "$OLLAMA_API_BASE" "$MODE_LABEL"
fi

CMD=(python3 -m aider --no-check-update --no-show-release-notes --analytics-disable --no-auto-commits --no-dirty-commits --yes-always --no-fancy-input --no-browser)
[ "$HAS_MODEL_OVERRIDE" -eq 1 ] || CMD+=(--model "$MODEL")
[ "$HAS_MAP_TOKENS_OVERRIDE" -eq 1 ] || CMD+=(--map-tokens "$MAP_TOKENS")
[ "$HAS_TIMEOUT_OVERRIDE" -eq 1 ] || CMD+=(--timeout "$TIMEOUT")

if [ "${#PASSTHRU_ARGS[@]}" -gt 0 ]; then
  CMD+=("${PASSTHRU_ARGS[@]}")
fi

EFFECTIVE_MODEL="${USER_MODEL:-$MODEL}"
EFFECTIVE_MAP_TOKENS="${USER_MAP_TOKENS:-$MAP_TOKENS}"
EFFECTIVE_TIMEOUT="${USER_TIMEOUT:-$TIMEOUT}"

echo "[aider-local] OLLAMA_API_BASE=$OLLAMA_API_BASE"
echo "[aider-local] model=$EFFECTIVE_MODEL map_tokens=$EFFECTIVE_MAP_TOKENS timeout=$EFFECTIVE_TIMEOUT"
printf '[aider-local] exec:'
for a in "${CMD[@]}"; do
  printf ' [%s]' "$a"
done
printf '\n'

export AIDER_SUP_MODE="$MODE_LABEL"
export AIDER_SUP_LABEL="${AIDER_SUP_LABEL:-$MODE_LABEL}"
export AIDER_SUP_MODEL="$EFFECTIVE_MODEL"
export AIDER_SUP_MAP_TOKENS="$EFFECTIVE_MAP_TOKENS"
export AIDER_SUP_TIMEOUT="$EFFECTIVE_TIMEOUT"
export AIDER_SUP_WRAP_TIMEOUT="${AIDER_SUP_WRAP_TIMEOUT:-$EFFECTIVE_TIMEOUT}"
export AIDER_SUP_TIMEOUT_FLAG="$EFFECTIVE_TIMEOUT"
export AIDER_SUP_API_BASE="$OLLAMA_API_BASE"
SUPERVISOR="$BASE_DIR/aider_failure_supervisor.sh"
if [ -f "$SUPERVISOR" ]; then
  exec bash "$SUPERVISOR" "${CMD[@]}"
fi
exec "${CMD[@]}"
