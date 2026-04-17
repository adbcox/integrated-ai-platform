from typing import Any


def report_phase5_capstone_closure(
    capstone_summary: dict[str, Any],
    closure_summary: dict[str, Any],
    phase_id: str,
) -> dict[str, Any]:
    if (
        not isinstance(capstone_summary, dict)
        or not isinstance(closure_summary, dict)
        or not isinstance(phase_id, str)
    ):
        return {
            "capstone_closure_report_status": "failed",
            "closure_report_phase": None,
            "closure_report_completeness": 0,
        }

    capstone_ok = capstone_summary.get("capstone_summary_status") == "complete"
    closure_ok = closure_summary.get("closure_summary_status") == "complete"

    if capstone_ok and closure_ok:
        return {
            "capstone_closure_report_status": "complete",
            "closure_report_phase": capstone_summary.get("capstone_phase"),
            "closure_report_completeness": 100,
        }

    return {
        "capstone_closure_report_status": "incomplete",
        "closure_report_phase": None,
        "closure_report_completeness": 0,
    }
