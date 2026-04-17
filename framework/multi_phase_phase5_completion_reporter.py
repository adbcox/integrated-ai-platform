from typing import Any


def report_phase5_completion(
    phase5_closure_gate: dict[str, Any],
    report_config: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(phase5_closure_gate, dict)
        or not isinstance(report_config, dict)
    ):
        return {
            "phase5_completion_status": "invalid_input",
            "completion_phase": None,
            "completion_detail": None,
        }

    pcg_ok = phase5_closure_gate.get("phase5_closure_status") == "closed"

    if pcg_ok:
        return {
            "phase5_completion_status": "complete",
            "completion_phase": phase5_closure_gate.get("closure_phase"),
            "completion_detail": "phase5_fully_complete",
        }

    return {
        "phase5_completion_status": "incomplete",
        "completion_phase": None,
        "completion_detail": "phase5_not_closed",
    }
