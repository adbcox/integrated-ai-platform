from typing import Any


def report_self_evaluation(
    self_evaluation_auditor: dict[str, Any],
    robustness_score: dict[str, Any],
    phase_id: str,
) -> dict[str, Any]:
    if (
        not isinstance(self_evaluation_auditor, dict)
        or not isinstance(robustness_score, dict)
        or not isinstance(phase_id, str)
    ):
        return {
            "self_eval_report_status": "invalid_input",
            "report_phase": None,
            "report_detail": None,
        }

    sea_ok = self_evaluation_auditor.get("self_eval_audit_status") == "passed"
    rs_ok = robustness_score.get("robustness_status") == "scored"
    all_ok = sea_ok and rs_ok

    if all_ok:
        return {
            "self_eval_report_status": "complete",
            "report_phase": phase_id,
            "report_detail": "self_evaluation_reported",
        }

    return {
        "self_eval_report_status": "incomplete",
        "report_phase": None,
        "report_detail": None,
    }
