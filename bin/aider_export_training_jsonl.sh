#!/bin/sh
set -eu

BASE_DIR="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
DATA_DIR="$BASE_DIR/.local-model-data"
OUT_FILE="$BASE_DIR/.local-model-data/training_corpus.jsonl"

usage() {
  cat <<'USAGE'
Usage:
  ./bin/aider_export_training_jsonl.sh [--data-dir <path>] [--out-file <path>]

Exports local feedback samples into newline-delimited JSON for future tuning workflows.
USAGE
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --data-dir)
      DATA_DIR="${2:-}"
      shift 2
      ;;
    --out-file)
      OUT_FILE="${2:-}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "ERROR: unknown argument: $1" >&2
      usage
      exit 1
      ;;
  esac
done

mkdir -p "$(dirname "$OUT_FILE")"
: >"$OUT_FILE"

if [ ! -d "$DATA_DIR" ]; then
  echo "No training data directory found: $DATA_DIR"
  exit 0
fi

json_escape_file() {
  in_file="$1"
  if [ ! -f "$in_file" ]; then
    printf ''
    return 0
  fi
  sed -e 's/\\/\\\\/g' -e 's/"/\\"/g' -e ':a;N;$!ba;s/\n/\\n/g' "$in_file"
}

for rec in "$DATA_DIR"/*; do
  [ -d "$rec" ] || continue
  meta="$(json_escape_file "$rec/meta.txt")"
  summary="$(json_escape_file "$rec/summary.md")"
  outcome="$(json_escape_file "$rec/outcome.md")"
  checks="$(json_escape_file "$rec/checks.txt")"
  changed="$(json_escape_file "$rec/changed_files.txt")"

  printf '{"record":"%s","meta":"%s","summary":"%s","outcome":"%s","checks":"%s","changed_files":"%s"}\n' \
    "$(basename "$rec")" "$meta" "$summary" "$outcome" "$checks" "$changed" >>"$OUT_FILE"
done

echo "Exported training data JSONL: $OUT_FILE"
