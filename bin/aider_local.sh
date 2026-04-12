#!/usr/bin/env bash
set -euo pipefail

API_BASE="http://127.0.0.1:11535"
MODEL="ollama_chat/qwen2.5-coder:1.5b"
MAP_TOKENS="0"
TIMEOUT="60"
HAS_MODEL_OVERRIDE=0
HAS_MAP_TOKENS_OVERRIDE=0
HAS_TIMEOUT_OVERRIDE=0

usage() {
  cat <<'USAGE'
Usage:
  ./bin/aider_local.sh [--hard] [--gpu-experimental] [--api-base <url>] [aider args...]

Default fast tactical settings:
  OLLAMA_API_BASE=http://127.0.0.1:11535
  --model ollama_chat/qwen2.5-coder:1.5b
  --map-tokens 0
  --timeout 60

Options:
  --hard               Use explicit harder-task profile (7b, map-tokens 1024, timeout 120)
  --gpu-experimental   Route to GPU endpoint (127.0.0.1:11434). Experimental only.
  --api-base <url>     Override Ollama API base URL
  -h, --help           Show help
USAGE
}

EXTRA_ARGS=""
while [ "$#" -gt 0 ]; do
  case "$1" in
    --hard)
      MODEL="ollama_chat/qwen2.5-coder:7b"
      MAP_TOKENS="1024"
      TIMEOUT="120"
      shift
      ;;
    --gpu-experimental)
      API_BASE="http://127.0.0.1:11434"
      shift
      ;;
    --api-base)
      API_BASE="${2:-}"
      [ -n "$API_BASE" ] || { echo "ERROR: --api-base requires a value" >&2; exit 1; }
      shift 2
      ;;
    --model)
      HAS_MODEL_OVERRIDE=1
      EXTRA_ARGS="$EXTRA_ARGS
$1
${2:-}"
      shift 2
      ;;
    --model=*)
      HAS_MODEL_OVERRIDE=1
      EXTRA_ARGS="$EXTRA_ARGS
$1"
      shift
      ;;
    --map-tokens)
      HAS_MAP_TOKENS_OVERRIDE=1
      EXTRA_ARGS="$EXTRA_ARGS
$1
${2:-}"
      shift 2
      ;;
    --map-tokens=*)
      HAS_MAP_TOKENS_OVERRIDE=1
      EXTRA_ARGS="$EXTRA_ARGS
$1"
      shift
      ;;
    --timeout)
      HAS_TIMEOUT_OVERRIDE=1
      EXTRA_ARGS="$EXTRA_ARGS
$1
${2:-}"
      shift 2
      ;;
    --timeout=*)
      HAS_TIMEOUT_OVERRIDE=1
      EXTRA_ARGS="$EXTRA_ARGS
$1"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      EXTRA_ARGS="$EXTRA_ARGS
$1"
      shift
      ;;
  esac
done

export OLLAMA_API_BASE="$API_BASE"

set -- aider
[ "$HAS_MODEL_OVERRIDE" -eq 1 ] || set -- "$@" --model "$MODEL"
[ "$HAS_MAP_TOKENS_OVERRIDE" -eq 1 ] || set -- "$@" --map-tokens "$MAP_TOKENS"
[ "$HAS_TIMEOUT_OVERRIDE" -eq 1 ] || set -- "$@" --timeout "$TIMEOUT"

while IFS= read -r arg; do
  [ -n "$arg" ] || continue
  set -- "$@" "$arg"
done <<EOF
$EXTRA_ARGS
EOF

echo "[aider-local] OLLAMA_API_BASE=$OLLAMA_API_BASE"
echo "[aider-local] model=$MODEL map_tokens=$MAP_TOKENS timeout=$TIMEOUT"
printf '[aider-local] exec:'
for a in "$@"; do
  printf ' [%s]' "$a"
done
printf '\n'
exec "$@"
