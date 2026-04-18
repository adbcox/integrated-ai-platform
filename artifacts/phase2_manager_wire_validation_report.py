"""Validation report for phase2_manager_wire: control-plane Phase 2 consumption."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from framework.runtime_validation_pack import (
    assert_phase2_manager_wire_present,
    run_phase2_manager_wire_validation,
)


def generate_phase2_manager_wire_validation_report() -> dict:
    error_msg = ""
    manager_view: dict = {}

    try:
        with tempfile.TemporaryDirectory(prefix="p2_mgr_wire_") as tmp:
            result = run_phase2_manager_wire_validation(base_root=Path(tmp))

        errors = assert_phase2_manager_wire_present(result)
        if errors:
            error_msg = "; ".join(errors)

        manager_view = result.get("manager_view") or {}
    except Exception as exc:
        error_msg = str(exc)

    manager_view_present = bool(manager_view)
    canonical_session_summary = manager_view.get("canonical_session_summary") or {}
    canonical_job_summaries = manager_view.get("canonical_job_summaries")
    typed_tool_summary = manager_view.get("typed_tool_summary") or {}
    permission_decision_count = manager_view.get("permission_decision_count")
    final_outcome = manager_view.get("final_outcome")

    canonical_session_summary_present = bool(canonical_session_summary)
    canonical_job_summaries_present = isinstance(canonical_job_summaries, list)
    typed_tool_summary_present = bool(typed_tool_summary)
    permission_decision_count_present = permission_decision_count is not None
    final_outcome_present = final_outcome is not None
    tool_count_ge_1 = (typed_tool_summary.get("tool_count") or 0) >= 1

    all_checks_pass = (
        not error_msg
        and manager_view_present
        and canonical_session_summary_present
        and canonical_job_summaries_present
        and typed_tool_summary_present
        and permission_decision_count_present
        and final_outcome_present
        and tool_count_ge_1
    )

    return {
        "phase2_manager_wire_check": "phase2_manager_wire",
        "manager_view_present": manager_view_present,
        "canonical_session_summary_present": canonical_session_summary_present,
        "canonical_job_summaries_present": canonical_job_summaries_present,
        "typed_tool_summary_present": typed_tool_summary_present,
        "permission_decision_count_present": permission_decision_count_present,
        "final_outcome_present": final_outcome_present,
        "tool_count_ge_1": tool_count_ge_1,
        "error": error_msg,
        "all_checks_pass": all_checks_pass,
        "status": "pass" if all_checks_pass else "fail",
    }


if __name__ == "__main__":
    report = generate_phase2_manager_wire_validation_report()
    print(json.dumps(report, indent=2))
    sys.exit(0 if report.get("all_checks_pass") else 1)
