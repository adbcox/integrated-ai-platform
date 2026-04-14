#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"  # stage7-op
cd "$REPO_ROOT"

PLAN_ID="stage7-regression-$(date +%s)"
python3 bin/stage7_manager.py \
  --query "stage7 manager rag multi plan" \
  --plan-id "$PLAN_ID" \
  --commit-msg "stage7 micro regression" \
  --max-subplans 2 \
  --subplan-size 2 \
  --max-entries-per-subplan 2 \
  --subplan-failure-policy split_on_failure \
  --dry-run

echo "stage7 regression dry-run completed: $PLAN_ID"
