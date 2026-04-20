#!/usr/bin/env python3
"""Apply promotion/demotion/hold decisions from unified Level-10 qualification."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from _datetime_compat import UTC
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from promotion import MANIFEST_PATH, load_manifest  # noqa: E402

LEVEL10_QUALIFY = REPO_ROOT / "bin" / "level10_qualify.py"
DECISION_DIR = REPO_ROOT / "artifacts" / "promotion"
DECISION_HISTORY = DECISION_DIR / "decision_history.jsonl"


@dataclass
class LaneDecision:
    lane: str
    action: str
    reason: str
    next_status: str


def now_utc() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def run_level10_qualify(manifest_path: Path) -> dict[str, Any]:
    cmd = [sys.executable, str(LEVEL10_QUALIFY), "--manifest", str(manifest_path), "--json"]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return json.loads(proc.stdout)


def _candidate_decision(summary: dict[str, Any], criteria: dict[str, Any], current_status: str) -> LaneDecision:
    metrics = summary.get("metrics", {}).get("candidate", {})
    recovery = summary.get("metrics", {}).get("candidate_recovery", {})
    success = int(metrics.get("success", 0))
    failure = int(metrics.get("failure", 0))
    success_streak = int(recovery.get("latest_success_streak", 0))
    success_threshold = int(criteria.get("candidate_success_threshold", 0))
    failure_budget = int(criteria.get("candidate_failure_budget", 0))
    recovery_streak_threshold = int(criteria.get("candidate_recovery_streak_threshold", 0))
    recovery_failure_cap = int(criteria.get("candidate_recovery_failure_cap", 0))

    if success >= success_threshold and failure <= failure_budget:
        return LaneDecision(
            lane="candidate",
            action="promote",
            reason=(
                f"candidate success/failure {success}/{failure} meets "
                f"threshold {success_threshold} and budget {failure_budget}"
            ),
            next_status="ready_for_promotion",
        )
    if (
        recovery_streak_threshold > 0
        and recovery_failure_cap > 0
        and success >= success_threshold
        and success_streak >= recovery_streak_threshold
        and failure <= recovery_failure_cap
    ):
        return LaneDecision(
            lane="candidate",
            action="promote",
            reason=(
                f"candidate recovery rule met: streak {success_streak}>={recovery_streak_threshold}, "
                f"success/failure {success}/{failure}, failure_cap={recovery_failure_cap}"
            ),
            next_status="ready_for_promotion",
        )
    if failure > max(1, failure_budget * 2) and success < success_threshold:
        return LaneDecision(
            lane="candidate",
            action="demote",
            reason=(
                f"candidate failure count {failure} exceeds hard demotion threshold "
                f"{failure_budget * 2} without enough successes ({success}/{success_threshold})"
            ),
            next_status="blocked",
        )
    return LaneDecision(
        lane="candidate",
        action="hold",
        reason=(
            f"candidate success/failure {success}/{failure} does not satisfy "
            f"promotion or demotion thresholds"
        ),
        next_status=current_status,
    )


def _preview_decision(summary: dict[str, Any], criteria: dict[str, Any], current_status: str) -> LaneDecision:
    metrics = summary.get("metrics", {}).get("stage6_preview", {})
    stage6_success = int(metrics.get("success", 0))
    stage6_failure = int(metrics.get("failure", 0))
    stage6_success_threshold = int(criteria.get("stage6_success_threshold", 0))
    stage6_failure_budget = int(criteria.get("stage6_failure_budget", 0))
    assessments = summary.get("subsystem_assessments", {})
    core_ready = all(
        bool(assessments.get(name, {}).get("evidence_met"))
        for name in ("stage_system", "manager_system", "rag_system", "regression_framework", "gate_chain")
    )

    if core_ready and stage6_success >= stage6_success_threshold and stage6_failure <= stage6_failure_budget:
        return LaneDecision(
            lane="stage6",
            action="promote",
            reason=(
                "core subsystem evidence is ready and "
                f"stage6 success/failure {stage6_success}/{stage6_failure} meets "
                f"{stage6_success_threshold}/{stage6_failure_budget}"
            ),
            next_status="candidate_ready",
        )
    if stage6_failure > max(1, stage6_failure_budget * 2) and stage6_success == 0:
        return LaneDecision(
            lane="stage6",
            action="demote",
            reason=(
                f"stage6 failures {stage6_failure} exceed hard demotion threshold "
                f"{stage6_failure_budget * 2} with zero successes"
            ),
            next_status="paused",
        )
    return LaneDecision(
        lane="stage6",
        action="hold",
        reason=(
            f"stage6 success/failure {stage6_success}/{stage6_failure} and "
            f"core_ready={core_ready} are not sufficient for promotion"
        ),
        next_status=current_status,
    )


def compute_decisions(summary: dict[str, Any], manifest_data: dict[str, Any]) -> list[LaneDecision]:
    criteria = manifest_data.get("promotion_policy", {}).get("criteria", {})
    lanes = manifest_data.get("lanes", {})
    candidate_status = str(lanes.get("candidate", {}).get("status", "in_progress"))
    preview_status = str(lanes.get("stage6", {}).get("status", "preview"))
    return [
        _candidate_decision(summary, criteria, candidate_status),
        _preview_decision(summary, criteria, preview_status),
    ]


def build_subsystem_gate_matrix(summary: dict[str, Any]) -> dict[str, Any]:
    v8 = summary.get("v8_gate_assertions", {}) if isinstance(summary.get("v8_gate_assertions"), dict) else {}
    gates = v8.get("gates", {}) if isinstance(v8.get("gates"), dict) else {}
    matrix = {
        "candidate_promote_requires": {
            "promotion8_ready": bool(gates.get("promotion8_ready")),
            "qualification8_ready": bool(gates.get("qualification8_ready")),
            "gate_chain_ready": bool(gates.get("gate_chain_ready")),
        },
        "stage6_promote_requires": {
            "stage8_ready": bool(gates.get("stage8_ready")),
            "manager8_ready": bool(gates.get("manager8_ready")),
            "rag8_ready": bool(gates.get("rag8_ready")),
            "worker8_ready": bool(gates.get("worker8_ready")),
            "qualification8_ready": bool(gates.get("qualification8_ready")),
            "gate_chain_ready": bool(gates.get("gate_chain_ready")),
        },
    }
    matrix["candidate_promote_blocked"] = [k for k, ok in matrix["candidate_promote_requires"].items() if not ok]
    matrix["stage6_promote_blocked"] = [k for k, ok in matrix["stage6_promote_requires"].items() if not ok]
    return matrix


def enforce_subsystem_gate_policy(decisions: list[LaneDecision], gate_matrix: dict[str, Any]) -> list[LaneDecision]:
    revised: list[LaneDecision] = []
    for decision in decisions:
        if decision.action != "promote":
            revised.append(decision)
            continue
        if decision.lane == "candidate":
            blocked = gate_matrix.get("candidate_promote_blocked", [])
            if blocked:
                revised.append(
                    LaneDecision(
                        lane=decision.lane,
                        action="hold",
                        reason=f"candidate promotion blocked by subsystem gates: {', '.join(blocked)}",
                        next_status=decision.next_status if decision.next_status != "ready_for_promotion" else "in_progress",
                    )
                )
                continue
        if decision.lane == "stage6":
            blocked = gate_matrix.get("stage6_promote_blocked", [])
            if blocked:
                revised.append(
                    LaneDecision(
                        lane=decision.lane,
                        action="hold",
                        reason=f"stage6 promotion blocked by subsystem gates: {', '.join(blocked)}",
                        next_status=decision.next_status if decision.next_status != "candidate_ready" else "building",
                    )
                )
                continue
        revised.append(decision)
    return revised


def write_audit_record(record: dict[str, Any]) -> None:
    DECISION_DIR.mkdir(parents=True, exist_ok=True)
    with DECISION_HISTORY.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")


def apply_decisions(manifest_data: dict[str, Any], decisions: list[LaneDecision], timestamp: str) -> None:
    lanes = manifest_data.setdefault("lanes", {})
    for decision in decisions:
        lane_cfg = lanes.get(decision.lane)
        if not isinstance(lane_cfg, dict):
            continue
        lane_cfg["status"] = decision.next_status

    policy = manifest_data.setdefault("promotion_policy", {})
    history = policy.setdefault("history", [])
    history.append(
        {
            "date": timestamp,
            "type": "level10_control_loop",
            "decisions": [decision.__dict__ for decision in decisions],
        }
    )
    policy["last_decision"] = {
        "date": timestamp,
        "status": "level10_control_loop_applied",
        "notes": "; ".join(f"{d.lane}:{d.action}" for d in decisions),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Apply Level-10 promotion/demotion control loop")
    parser.add_argument("--manifest", default=str(MANIFEST_PATH) , help="Promotion manifest path")
    parser.add_argument("--dry-run", action="store_true", help="Compute and log decisions without mutating manifest")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_path = Path(args.manifest).resolve()
    manifest_cfg = load_manifest(manifest_path)
    manifest_data = manifest_cfg.data
    summary = run_level10_qualify(manifest_path)
    gate_matrix = build_subsystem_gate_matrix(summary)
    decisions = enforce_subsystem_gate_policy(compute_decisions(summary, manifest_data), gate_matrix)
    timestamp = now_utc()

    audit_record = {
        "timestamp": timestamp,
        "manifest_path": str(manifest_path),
        "manifest_version_before": manifest_cfg.version,
        "dry_run": bool(args.dry_run),
        "decisions": [decision.__dict__ for decision in decisions],
        "metrics": summary.get("metrics", {}),
        "gate_chain_stats": summary.get("metrics", {}).get("gate_chain", {}),
        "subsystem_assessments": summary.get("subsystem_assessments", {}),
        "subsystem_gate_matrix": gate_matrix,
    }

    if args.dry_run:
        audit_record["result"] = "no_manifest_changes"
        write_audit_record(audit_record)
        print(json.dumps(audit_record, ensure_ascii=False, indent=2))
        return 0

    apply_decisions(manifest_data, decisions, timestamp)
    manifest_path.write_text(json.dumps(manifest_data, ensure_ascii=False, indent=4) + "\n", encoding="utf-8")
    audit_record["manifest_version_after"] = int(manifest_data.get("version", 0))
    audit_record["result"] = "manifest_updated"
    write_audit_record(audit_record)
    print(json.dumps(audit_record, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":  # entrypoint
    raise SystemExit(main())
