#!/usr/bin/env python3
"""Phase 2 runtime wire validation report."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from framework.runtime_validation_pack import (  # noqa: E402
    REQUIRED_PHASE2_RUNTIME_KEYS,
    run_phase2_runtime_wire_validation,
)


def _check_payload_shape(payload: dict[str, Any]) -> bool:
    if not REQUIRED_PHASE2_RUNTIME_KEYS.issubset(payload.keys()):
        return False
    if not isinstance(payload.get("canonical_session"), dict):
        return False
    if not isinstance(payload.get("canonical_jobs"), list) or not payload["canonical_jobs"]:
        return False
    if not isinstance(payload.get("typed_tool_trace"), list):
        return False
    if not isinstance(payload.get("session_bundle"), dict):
        return False
    return True


def _has_blocked_run_command(payload: dict[str, Any]) -> bool:
    for entry in payload.get("typed_tool_trace", []):
        if not isinstance(entry, dict):
            continue
        if entry.get("kind") != "tool_observation":
            continue
        if (
            entry.get("status") == "blocked"
            and entry.get("allowed") is False
            and entry.get("tool_name") == "run_command"
        ):
            return True
    return False


def generate_phase2_runtime_wire_validation_report() -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="phase2-wire-allow-") as td:
        allow_payload = run_phase2_runtime_wire_validation(
            allow_run_command=True, tmp_root=Path(td)
        )
    with tempfile.TemporaryDirectory(prefix="phase2-wire-block-") as td:
        block_payload = run_phase2_runtime_wire_validation(
            allow_run_command=False, tmp_root=Path(td)
        )

    allow_shape_ok = _check_payload_shape(allow_payload)
    block_shape_ok = _check_payload_shape(block_payload)
    allow_final_completed = allow_payload.get("final_outcome") == "completed"
    block_has_blocked = _has_blocked_run_command(block_payload)
    allow_persisted = allow_payload.get("__persisted", {})
    block_persisted = block_payload.get("__persisted", {})
    allow_persisted_flag = bool(allow_persisted.get("phase2_payload_present"))
    block_persisted_flag = bool(block_persisted.get("phase2_payload_present"))

    all_checks_pass = (
        allow_shape_ok
        and block_shape_ok
        and allow_final_completed
        and block_has_blocked
        and allow_persisted_flag
        and block_persisted_flag
    )

    return {
        "phase2_runtime_wire_check": "phase2_runtime_wire",
        "allow_shape_ok": allow_shape_ok,
        "block_shape_ok": block_shape_ok,
        "allow_final_outcome_completed": allow_final_completed,
        "block_has_blocked_run_command": block_has_blocked,
        "allow_persisted_phase2_flag": allow_persisted_flag,
        "block_persisted_phase2_flag": block_persisted_flag,
        "all_checks_pass": all_checks_pass,
        "status": "pass" if all_checks_pass else "fail",
    }


if __name__ == "__main__":
    report = generate_phase2_runtime_wire_validation_report()
    print(report)
    sys.exit(0 if report.get("all_checks_pass") else 1)
