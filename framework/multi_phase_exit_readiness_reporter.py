from typing import Any


def report_exit_readiness(
    exit_readiness_validator: dict[str, Any],
    self_evaluation_auditor: dict[str, Any],
    phase_id: str,
) -> dict[str, Any]:
    if (
        not isinstance(exit_readiness_validator, dict)
        or not isinstance(self_evaluation_auditor, dict)
        or not isinstance(phase_id, str)
    ):
        return {
            "exit_readiness_report_status": "invalid_input",
            "report_phase": None,
            "report_detail": None,
        }

    erv_ok = exit_readiness_validator.get("exit_readiness_status") == "valid"
    sea_ok = self_evaluation_auditor.get("self_eval_audit_status") == "passed"
    all_ok = erv_ok and sea_ok

    if all_ok:
        return {
            "exit_readiness_report_status": "complete",
            "report_phase": phase_id,
            "report_detail": "exit_readiness_reported",
        }

    return {
        "exit_readiness_report_status": "incomplete",
        "report_phase": None,
        "report_detail": None,
    }
