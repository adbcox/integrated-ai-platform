#!/usr/bin/env python3
"""Standalone validation report for PHASE2-EXIT-WIRE-1.

Exercises _compute_phase2_exit_code with all four exit-code branches and
reports pass/fail without requiring a live runtime.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from bin.framework_control_plane import _compute_phase2_exit_code


def _out(*, idle: bool, signal: str) -> dict:
    return {"idle_reached": idle, "phase2_operational_signal": {"signal": signal}}


def _rows(status: str) -> list[dict]:
    return [{"result": {"status": status}}]


def generate_phase2_exit_wire_validation_report() -> dict:
    failures: list[str] = []

    cases = [
        ("exit_2_not_idle", _out(idle=False, signal="ok"), _rows("completed"), 2),
        ("exit_2_not_idle_blocked", _out(idle=False, signal="all_tools_blocked"), _rows("completed"), 2),
        ("exit_3_non_terminal", _out(idle=True, signal="ok"), _rows("pending"), 3),
        ("exit_3_empty_rows", _out(idle=True, signal="ok"), [], 3),
        ("exit_4_all_tools_blocked", _out(idle=True, signal="all_tools_blocked"), _rows("completed"), 4),
        ("exit_4_escalated_blocked", _out(idle=True, signal="all_tools_blocked"), _rows("escalated"), 4),
        ("exit_0_ok_signal", _out(idle=True, signal="ok"), _rows("completed"), 0),
        ("exit_0_no_tools_ran", _out(idle=True, signal="no_tools_ran"), _rows("completed"), 0),
        ("exit_0_partial_block", _out(idle=True, signal="partial_block"), _rows("completed"), 0),
        ("exit_0_phase2_absent", _out(idle=True, signal="phase2_absent"), _rows("completed"), 0),
        ("exit_0_failed_status", _out(idle=True, signal="ok"), _rows("failed"), 0),
    ]

    for name, output, rows, expected in cases:
        actual = _compute_phase2_exit_code(output, rows)
        if actual != expected:
            failures.append(f"{name}: expected={expected} got={actual}")

    helper_importable = True
    try:
        from bin.framework_control_plane import _compute_phase2_exit_code as _check  # noqa: F401
    except ImportError as exc:
        helper_importable = False
        failures.append(f"import_failed: {exc}")

    all_checks_pass = len(failures) == 0
    return {
        "status": "pass" if all_checks_pass else "fail",
        "all_checks_pass": all_checks_pass,
        "helper_importable": helper_importable,
        "cases_checked": len(cases),
        "failures": failures,
    }


if __name__ == "__main__":
    import json

    report = generate_phase2_exit_wire_validation_report()
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not report["all_checks_pass"]:
        sys.exit(1)
