#!/bin/sh
set -eu

BASE_DIR="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
OFFLINE_MODE="changed"

usage() {
  cat <<'USAGE'
Usage:
  ./bin/remote_finalize.sh [--offline changed|full|skip]

Behavior:
  - always runs: make quick
  - --offline changed (default): make test-changed-offline
  - --offline full: make test-offline
  - --offline skip: no offline behavior tests
USAGE
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --offline)
      OFFLINE_MODE="${2:-}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "ERROR: unknown argument: $1 (Stage-3/Stage-4 finalize helper)" >&2
      echo "HINT: this lane expects bounded literal probes before remote finalize." >&2
      usage
      exit 1
      ;;
  esac
done

cd "$BASE_DIR"

echo "[finalize] Running quick guard checks..."
make quick

case "$OFFLINE_MODE" in
  changed)
    echo "[finalize] Running changed-scope offline tests..."
    make test-changed-offline
    ;;
  full)
    echo "[finalize] Running full-scope offline tests..."
    make test-offline
    ;;
  skip)
    echo "[finalize] Offline tests skipped upon request."
    ;;
  *)
    echo "ERROR: invalid --offline mode: $OFFLINE_MODE" >&2
    exit 1
    ;;
esac

echo "PASS: remote finalize checks complete."
