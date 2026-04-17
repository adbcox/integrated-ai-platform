from typing import Any


def report_phase5_exit_readiness(
    phase5_exit_finalizer: dict[str, Any],
    phase5_promotion_gate: dict[str, Any],
    phase_id: str,
) -> dict[str, Any]:
    if (
        not isinstance(phase5_exit_finalizer, dict)
        or not isinstance(phase5_promotion_gate, dict)
        or not isinstance(phase_id, str)
    ):
        return {
            "phase5_exit_report_status": "invalid_input",
            "report_phase": None,
            "report_detail": None,
        }

    pef_ok = phase5_exit_finalizer.get("exit_finalization_status") == "finalized"
    ppg_ok = phase5_promotion_gate.get("promotion_gate_status") == "promoted"
    all_ok = pef_ok and ppg_ok

    if all_ok:
        return {
            "phase5_exit_report_status": "complete",
            "report_phase": phase_id,
            "report_detail": "phase5_exit_ready",
        }

    return {
        "phase5_exit_report_status": "incomplete",
        "report_phase": None,
        "report_detail": None,
    }
