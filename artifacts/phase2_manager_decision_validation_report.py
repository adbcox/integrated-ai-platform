"""Validation report for phase2_manager_decision: control-plane operational signal."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from framework.runtime_validation_pack import (
    assert_phase2_manager_decision_present,
    run_phase2_manager_decision_validation,
)

_VALID_SIGNALS = frozenset(
    {"ok", "all_tools_blocked", "no_tools_ran", "partial_block", "phase2_absent"}
)


def generate_phase2_manager_decision_validation_report() -> dict:
    error_msg = ""
    manager_view: dict = {}
    operational_signal: dict = {}

    try:
        with tempfile.TemporaryDirectory(prefix="p2_mgr_decision_") as tmp:
            result = run_phase2_manager_decision_validation(base_root=Path(tmp))

        errors = assert_phase2_manager_decision_present(result)
        if errors:
            error_msg = "; ".join(errors)

        manager_view = result.get("manager_view") or {}
        operational_signal = result.get("operational_signal") or {}
    except Exception as exc:
        error_msg = str(exc)

    manager_view_present = bool(manager_view)
    operational_signal_present = bool(operational_signal)
    signal_value = operational_signal.get("signal") or ""
    signal_value_valid = signal_value in _VALID_SIGNALS
    phase2_payload_present = bool(manager_view.get("phase2_payload_present"))

    all_checks_pass = (
        not error_msg
        and manager_view_present
        and operational_signal_present
        and signal_value_valid
        and phase2_payload_present
    )

    return {
        "phase2_manager_decision_check": "phase2_manager_decision",
        "manager_view_present": manager_view_present,
        "operational_signal_present": operational_signal_present,
        "signal_value_valid": signal_value_valid,
        "signal_value": signal_value,
        "phase2_payload_present": phase2_payload_present,
        "error": error_msg,
        "all_checks_pass": all_checks_pass,
        "status": "pass" if all_checks_pass else "fail",
    }


if __name__ == "__main__":
    report = generate_phase2_manager_decision_validation_report()
    print(json.dumps(report, indent=2))
    sys.exit(0 if report.get("all_checks_pass") else 1)
