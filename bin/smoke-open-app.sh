#!/bin/sh
set -euo

BASE_DIR="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$BASE_DIR"

./tests/run_offline_scenarios.sh \
  open-app-deep-loaded \
  open-app-modal-blocked \
  open-app-missing-session
