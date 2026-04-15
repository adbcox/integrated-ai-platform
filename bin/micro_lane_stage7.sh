#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"  # stage7-op  # stage7-op  # stage7-op  # stage7-op  # stage7-op  # stage7-op  # stage7-op  # stage7-op  # stage7-op  # stage7-op  # stage7-op  # stage7-op  # stage7-op  # stage7-op  # stage7-op  # stage7-op  # stage7-op  # stage7-op  # stage7-op  # stage7-op
cd "$REPO_ROOT"

usage() {
  cat <<'USAGE'
Usage: bin/micro_lane_stage7.sh

Runs deterministic Stage-8/Manager-8/RAG-8 operational regression assertions:
  1. Stage-7 orchestration pause checkpoint run
  2. Stage-7 orchestration resume/reconcile run
  3. Qualification gate assertions for Stage-8 readiness evidence

Requires a clean working tree and leaves the repository clean.
USAGE
}

ensure_clean_tree() {
  if [ -n "$(git status --short)" ]; then
    echo "ERROR: working tree must be clean before Stage-7 regressions." >&2
    git status --short >&2
    exit 1
  fi
}

if [ "${1:-}" = "--help" ]; then
  usage
  exit 0
fi

ensure_clean_tree

PLAN_ID="stage7-regression-$(date -u +%Y%m%d%H%M%S)-$RANDOM"
CHECKPOINT_PATH="$REPO_ROOT/artifacts/manager6/plans/$PLAN_ID/checkpoints.json"
HISTORY_PATH="$REPO_ROOT/artifacts/manager6/plans/$PLAN_ID.json"

python3 bin/stage7_manager.py \
  --query "stage7 manager rag multi plan" \
  --plan-id "$PLAN_ID" \
  --commit-msg "stage7 micro regression" \
  --max-subplans 2 \
  --subplan-size 2 \
  --max-entries-per-subplan 2 \
  --subplan-failure-policy split_on_failure \
  --dry-run \
  --stop-after-subplans 1

python3 - "$CHECKPOINT_PATH" "$HISTORY_PATH" <<'PY'
import json
import sys
from pathlib import Path

checkpoint_path = Path(sys.argv[1])
history_path = Path(sys.argv[2])
if not checkpoint_path.exists():
    raise SystemExit(f"missing checkpoint file: {checkpoint_path}")
if not history_path.exists():
    raise SystemExit(f"missing plan history file: {history_path}")

checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
subplans = checkpoint.get("subplans") or {}
if not isinstance(subplans, dict) or not subplans:
    raise SystemExit("checkpoint file does not contain persisted subplan entries")

history = json.loads(history_path.read_text(encoding="utf-8"))
events = history.get("history") or []
if not any(e.get("event_type") == "attempt_paused" for e in events if isinstance(e, dict)):
    raise SystemExit("expected paused event not found in plan history")
PY

python3 bin/stage7_manager.py \
  --query "stage7 manager rag multi plan" \
  --plan-id "$PLAN_ID" \
  --commit-msg "stage7 micro regression" \
  --max-subplans 2 \
  --subplan-size 2 \
  --max-entries-per-subplan 2 \
  --subplan-failure-policy split_on_failure \
  --dry-run \
  --resume

python3 - "$HISTORY_PATH" <<'PY'
import json
import sys
from pathlib import Path

history_path = Path(sys.argv[1])
history = json.loads(history_path.read_text(encoding="utf-8"))
events = [e for e in (history.get("history") or []) if isinstance(e, dict)]

if not any(e.get("event_type") == "attempt_resumed" for e in events):
    raise SystemExit("expected resume event not found in plan history")
finished = [e for e in events if e.get("event_type") == "attempt_finished"]
if not finished:
    raise SystemExit("expected finished event not found in plan history")
final_state = str(finished[-1].get("state") or "")
if final_state not in {"succeeded", "partial_success"}:
    raise SystemExit(f"unexpected final state: {final_state}")
PY

QUAL_JSON="$(mktemp)"
python3 bin/level10_qualify.py --json > "$QUAL_JSON"
python3 - "$QUAL_JSON" <<'PY'
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
metrics = payload.get("metrics", {})
stage8 = metrics.get("stage8") if isinstance(metrics, dict) else {}
if not isinstance(stage8, dict):
    raise SystemExit("missing stage8 metrics in qualification output")

required_metric_checks = {
    "resumed_runs": int(stage8.get("resumed_runs") or 0) > 0,
    "checkpointed_runs": int(stage8.get("checkpointed_runs") or 0) > 0,
    "executed_subplans": int(stage8.get("executed_subplans") or 0) > 0,
    "rollback_contract_coverage": float(stage8.get("rollback_contract_coverage") or 0.0) >= 1.0,
    "worker_budget_decisions": int(stage8.get("worker_budget_decisions") or 0) > 0,
}
failed_metrics = [name for name, ok in required_metric_checks.items() if not ok]
if failed_metrics:
    raise SystemExit(f"stage8 metric assertions failed: {failed_metrics}")

v8 = payload.get("v8_gate_assertions", {})
gates = v8.get("gates") if isinstance(v8, dict) else {}
required_gates = [
    "stage8_ready",
    "manager8_ready",
    "rag8_ready",
    "worker8_ready",
    "qualification8_ready",
]
failed_gates = [name for name in required_gates if not bool(gates.get(name))]
if failed_gates:
    raise SystemExit(f"required v8 gate assertions failed: {failed_gates}")
PY
rm -f "$QUAL_JSON"

ensure_clean_tree
echo "PASS: Stage-7 deterministic regression assertions completed: $PLAN_ID"
