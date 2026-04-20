#!/usr/bin/env python3
"""Phase 7 v8 gate evidence collector.

Orchestrates:
  1. qualify_v4_artifact_builder  — refresh benchmark + attribution from stage3 traces
  2. stage_rag6_plan_probe        — generate rag6 usage to satisfy rag8_ready
  3. level10_qualify --json       — evaluate all 9 v8 gates
  4. Write artifacts/phase7_evidence/latest.json
  5. Write governance/phase7_closure_evidence.json (if all_ready)
     or governance/phase7_partial_evidence.json (if gates remain open)
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

PHASE7_EVIDENCE_DIR = REPO_ROOT / "artifacts" / "phase7_evidence"
PHASE7_EVIDENCE_LATEST = PHASE7_EVIDENCE_DIR / "latest.json"
PHASE7_CLOSURE_EVIDENCE = REPO_ROOT / "governance" / "phase7_closure_evidence.json"
PHASE7_PARTIAL_EVIDENCE = REPO_ROOT / "governance" / "phase7_partial_evidence.json"

RAG6_PROBE_QUERIES = [
    "improve ExecutorFactory reliability",
    "where is manager orchestration code",
    "harden WorkerRuntime job execution",
]

GATE_GAP_DESCRIPTIONS: dict[str, str] = {
    "stage8_ready": (
        "Requires artifacts/manager6/traces.jsonl with stage8 rows containing "
        "extra.resume, extra.checkpoint_path, rollback_contract_coverage >= 1.0. "
        "Needs stage6_manager.py to execute a full stage8 orchestration run."
    ),
    "manager8_ready": (
        "Requires stage8 execution rows with extra.manager_decisions dict "
        "and manager5 plans with current_state + attempt_count set. "
        "Blocked on same stage8 infrastructure as stage8_ready."
    ),
    "rag8_ready": (
        "Requires artifacts/stage_rag6/usage.jsonl with plan rows containing "
        "subplans with risk_score+conflict_signals and yield_score. "
        "Run stage_rag6_plan_probe.py against real queries."
    ),
    "worker8_ready": (
        "Requires stage8 subplan rows with worker_budget_decision populated. "
        "Blocked on stage8 infrastructure."
    ),
    "promotion8_ready": (
        "Requires candidate_success >= 4 within 7-day trace window (current: 0). "
        "Needs 4 successful stage4_manager candidate runs."
    ),
    "qualification8_ready": (
        "Requires promotion_engine.evidence_met (see promotion8_ready gap) "
        "plus version8_upgrade_list in manifest (present). "
        "Primary blocker is candidate run count."
    ),
    "gate_chain_ready": (
        "Requires stage3_manager trace rows with gates_run list of length 4 "
        "including g4_repo_quick, and target_test_discovery_mode != 'none'. "
        "Current trace row lacks gates_run field."
    ),
}


def _iso_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _run(argv: list[str], *, label: str) -> subprocess.CompletedProcess:
    print(f"[collect] {label} ...", flush=True)
    result = subprocess.run(argv, cwd=str(REPO_ROOT))
    status = "OK" if result.returncode == 0 else f"FAILED (rc={result.returncode})"
    print(f"[collect] {label}: {status}", flush=True)
    return result


def step_refresh_artifacts() -> None:
    _run(
        [sys.executable, str(REPO_ROOT / "bin" / "qualify_v4_artifact_builder.py")],
        label="qualify_v4_artifact_builder",
    )


def step_rag6_probes() -> None:
    probe = str(REPO_ROOT / "bin" / "stage_rag6_plan_probe.py")
    for i, query in enumerate(RAG6_PROBE_QUERIES):
        plan_id = f"p7-evidence-{i + 1:03d}"
        _run(
            [sys.executable, probe, "--plan-id", plan_id] + query.split(),
            label=f"stage_rag6_plan_probe: {query!r}",
        )


def step_evaluate_gates() -> tuple[dict, int]:
    print("[collect] level10_qualify --json ...", flush=True)
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "bin" / "level10_qualify.py"), "--json"],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    try:
        qualify_output = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        print(f"[collect] ERROR: level10_qualify JSON parse failed: {exc}", file=sys.stderr)
        print(f"[collect] stdout was: {result.stdout[:500]}", file=sys.stderr)
        sys.exit(1)
    print(f"[collect] level10_qualify: rc={result.returncode}", flush=True)
    return qualify_output, result.returncode


def write_phase7_evidence(qualify_output: dict, qualify_rc: int) -> dict:
    PHASE7_EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    v8 = qualify_output["v8_gate_assertions"]
    payload = {
        "schema_version": 1,
        "collected_at": _iso_now(),
        "v8_gates": v8["gates"],
        "all_ready": v8["all_ready"],
        "missing_gates": v8.get("missing", []),
        "metrics_snapshot": qualify_output.get("metrics", {}),
        "qualify_exit_code": qualify_rc,
    }
    PHASE7_EVIDENCE_LATEST.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"[collect] wrote {PHASE7_EVIDENCE_LATEST}", flush=True)
    return payload


def write_governance_closure(payload: dict) -> None:
    doc = {
        "schema_version": 1,
        "authority_owner": "governance",
        "closure_type": "full_closure",
        "collected_at": payload["collected_at"],
        "all_ready": True,
        "v8_gates": payload["v8_gates"],
        "metrics_snapshot": payload["metrics_snapshot"],
        "evidence_artifact": "artifacts/phase7_evidence/latest.json",
        "ratified_by": "collect_phase7_evidence.py",
    }
    PHASE7_CLOSURE_EVIDENCE.write_text(json.dumps(doc, indent=2), encoding="utf-8")
    print(f"[collect] wrote {PHASE7_CLOSURE_EVIDENCE}", flush=True)


def write_governance_partial(payload: dict) -> None:
    missing = payload["missing_gates"]
    open_gates = {
        gate: {
            "ready": False,
            "gap": GATE_GAP_DESCRIPTIONS.get(gate, "No gap description available."),
        }
        for gate in missing
    }
    ready_gates = [g for g, ready in payload["v8_gates"].items() if ready]
    doc = {
        "schema_version": 1,
        "authority_owner": "governance",
        "closure_type": "partial_evidence",
        "collected_at": payload["collected_at"],
        "all_ready": False,
        "ready_gates": ready_gates,
        "open_gates": open_gates,
        "missing_gate_count": len(missing),
        "ready_gate_count": len(ready_gates),
        "primary_blocker": "stage8 infrastructure (stage8_ready, manager8_ready, worker8_ready)",
        "next_session_type": "capability_session",
        "next_session_goal": (
            "Implement stage6_manager stage8 orchestration mode with "
            "checkpoint/resume/rollback traces; execute 4+ candidate promotion runs; "
            "run gate-chain validated stage3_manager jobs with gates_run populated."
        ),
        "evidence_artifact": "artifacts/phase7_evidence/latest.json",
    }
    PHASE7_PARTIAL_EVIDENCE.write_text(json.dumps(doc, indent=2), encoding="utf-8")
    print(f"[collect] wrote {PHASE7_PARTIAL_EVIDENCE}", flush=True)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Phase 7 v8 gate evidence collector")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Evaluate and print gate state; do not write governance files",
    )
    parser.add_argument(
        "--skip-rag6",
        action="store_true",
        help="Skip stage_rag6 probe invocation (offline/fast mode)",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()

    step_refresh_artifacts()

    if not args.skip_rag6:
        step_rag6_probes()
    else:
        print("[collect] --skip-rag6: skipping stage_rag6 probes", flush=True)

    qualify_output, qualify_rc = step_evaluate_gates()
    v8 = qualify_output["v8_gate_assertions"]

    print("\n[collect] === Gate Summary ===", flush=True)
    for gate, ready in v8["gates"].items():
        status = "READY" if ready else "OPEN"
        print(f"  {gate}: {status}", flush=True)
    print(f"\n[collect] all_ready: {v8['all_ready']}", flush=True)
    missing = v8.get("missing", [])
    if missing:
        print(f"[collect] missing gates: {missing}", flush=True)

    payload = write_phase7_evidence(qualify_output, qualify_rc)

    if args.dry_run:
        print("[collect] --dry-run: skipping governance file writes", flush=True)
        return 0

    if payload["all_ready"]:
        write_governance_closure(payload)
    else:
        write_governance_partial(payload)

    return 0


if __name__ == "__main__":
    sys.exit(main())
