#!/usr/bin/env python3
"""Assess local execution sovereignty for routine roadmap implementation."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
OUT = REPO_ROOT / "artifacts/autonomy/local_execution_sovereignty_verdict.json"
STATUS_SURFACE = REPO_ROOT / "governance/local_execution_sovereignty_status.v1.yaml"


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def main() -> int:
    evidence_paths = {
        "phase7_live_evidence": "artifacts/substrate/phase7_live_evidence_pack_check.json",
        "phase7_final_ratification": "artifacts/substrate/phase7_final_ratification_check.json",
        "autonomy_dashboard": "artifacts/local_autonomy_dashboard/local_autonomy_dashboard.json",
        "runtime_exec_validation": "artifacts/validation/phase1_runtime_execution_path_validation.json",
        "runtime_profiles": "governance/runtime_profiles.v1.yaml",
        "inference_gateway_impl": "framework/inference_gateway.py",
        "runtime_executor_impl": "runtime/runtime_executor.py",
    }
    resolved = {key: REPO_ROOT / rel for key, rel in evidence_paths.items()}

    file_existence = {
        key: path.exists() for key, path in resolved.items()
    }
    missing_files = [key for key, exists in file_existence.items() if not exists]

    blockers: list[dict[str, Any]] = []

    live_evidence = _read_json(resolved["phase7_live_evidence"]) if resolved["phase7_live_evidence"].exists() else {}
    final_ratification = _read_json(resolved["phase7_final_ratification"]) if resolved["phase7_final_ratification"].exists() else {}
    dashboard = _read_json(resolved["autonomy_dashboard"]) if resolved["autonomy_dashboard"].exists() else {}
    runtime_validation = _read_json(resolved["runtime_exec_validation"]) if resolved["runtime_exec_validation"].exists() else {}
    runtime_profiles = _read_yaml(resolved["runtime_profiles"]) if resolved["runtime_profiles"].exists() else {}

    if not live_evidence.get("live_dispatch_succeeded", False):
        blockers.append(
            {
                "blocker_id": "SOV-B01",
                "description": "Live local dispatch is not succeeding in current environment.",
                "why_blocks_sovereignty": "Routine roadmap execution cannot rely on a local-first path if live dispatch is blocked.",
                "evidence_files": [
                    evidence_paths["phase7_live_evidence"],
                ],
                "current_signal": {
                    "dispatch_mode": live_evidence.get("dispatch_mode"),
                    "blockers_remaining": live_evidence.get("blockers_remaining"),
                },
                "fixability": "fixable_with_local_model_runtime_configuration",
                "closure_condition": "phase7_live_evidence_pack_check.json reports live_dispatch_succeeded=true with no dispatch blocker.",
            }
        )

    if not final_ratification.get("promotion_gate_cleared", False):
        blockers.append(
            {
                "blocker_id": "SOV-B02",
                "description": "Final local autonomy/promotion gate is not cleared.",
                "why_blocks_sovereignty": "The authoritative ratification surface does not currently approve routine sovereign execution.",
                "evidence_files": [
                    evidence_paths["phase7_final_ratification"],
                ],
                "current_signal": {
                    "phase7_final_ratified": final_ratification.get("phase7_final_ratified"),
                    "remaining_blockers": final_ratification.get("remaining_blockers"),
                },
                "fixability": "dependent_on_SOV-B01",
                "closure_condition": "phase7_final_ratification_check.json reports promotion_gate_cleared=true and remaining_blockers=[].",
            }
        )

    runtime_checks = runtime_validation.get("validation_checks") or runtime_validation.get("checks") or {}
    runtime_slice_check = runtime_checks.get("execution_runtime_slice") or {}
    runtime_slice_passed = str(runtime_slice_check.get("status")) == "PASS"
    runtime_slice_msg = str(runtime_slice_check.get("message", ""))
    if not runtime_slice_passed or "status: success" not in runtime_slice_msg:
        blockers.append(
            {
                "blocker_id": "SOV-B04",
                "description": "Runtime executor validation passes without a successful execution outcome.",
                "why_blocks_sovereignty": "Routine implementation requires successful bounded execution, not only artifact emission on failed runs.",
                "evidence_files": [
                    evidence_paths["runtime_exec_validation"],
                    evidence_paths["runtime_executor_impl"],
                ],
                "current_signal": {
                    "status": runtime_slice_check.get("status"),
                    "message": runtime_slice_msg,
                },
                "fixability": "fixable_with_runtime_execution_path_hardening",
                "closure_condition": "Runtime execution-path validator enforces and reports successful bounded execution status.",
            }
        )

    hard_profile = ((runtime_profiles.get("profiles") or {}).get("hard") or {})
    if hard_profile.get("backend") != "ollama":
        blockers.append(
            {
                "blocker_id": "SOV-B05",
                "description": "Hard profile does not route to local backend.",
                "why_blocks_sovereignty": "Complex routine implementation path may require non-local backend, violating sovereignty target.",
                "evidence_files": [
                    evidence_paths["runtime_profiles"],
                ],
                "current_signal": {"hard_profile_backend": hard_profile.get("backend")},
                "fixability": "fixable_with_profile_policy_update",
                "closure_condition": "All routine execution profiles required for approved implementation work route to local backends.",
            }
        )

    if missing_files:
        blockers.append(
            {
                "blocker_id": "SOV-B99",
                "description": "Required evidence surfaces are missing.",
                "why_blocks_sovereignty": "Missing evidence prevents authoritative closure.",
                "evidence_files": missing_files,
                "fixability": "fixable_now",
                "closure_condition": "All required evidence surfaces exist and parse.",
            }
        )

    verdict = "YES" if not blockers else "NO"
    payload = {
        "schema_version": 1,
        "assessment_id": "LOCAL-EXECUTION-SOVEREIGNTY-CLOSEOUT-1",
        "generated_at": _iso_now(),
        "verdict": verdict,
        "routine_execution_sovereign": verdict == "YES",
        "decision_rule": "Sovereign only when routine bounded implementation can run local-first on critical path with reproducible validation and artifact-complete output.",
        "evidence_files": evidence_paths,
        "file_existence": file_existence,
        "blocker_count": len(blockers),
        "blockers": blockers,
        "advisory_signals": {
            "local_autonomy_dashboard": {
                "overall_health": dashboard.get("overall_health"),
                "overall_verdict": (dashboard.get("readiness_summary") or {}).get("overall_verdict"),
            }
        },
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    status_surface = {
        "schema_version": "1.0",
        "kind": "local_execution_sovereignty_status",
        "assessment_ref": str(OUT.relative_to(REPO_ROOT)),
        "updated_at": _iso_now(),
        "verdict": verdict,
        "routine_execution_sovereign": verdict == "YES",
        "critical_path_outside_models_allowed": verdict != "YES",
        "blocker_ids": [b["blocker_id"] for b in blockers],
    }
    STATUS_SURFACE.write_text(
        yaml.safe_dump(status_surface, sort_keys=False),
        encoding="utf-8",
    )

    print(f"artifact={OUT}")
    print(f"status_surface={STATUS_SURFACE}")
    print(f"verdict={verdict}")
    return 0 if verdict == "YES" else 2


if __name__ == "__main__":
    raise SystemExit(main())
