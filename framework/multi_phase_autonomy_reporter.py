from typing import Any


def report_autonomy(
    audit: dict[str, Any],
    decision_validation: dict[str, Any],
    phase_id: str,
) -> dict[str, Any]:
    if (
        not isinstance(audit, dict)
        or not isinstance(decision_validation, dict)
        or not isinstance(phase_id, str)
        or not phase_id
    ):
        return {
            "autonomy_report_status": "invalid_input",
            "report_phase": None,
            "audit_ok_count": 0,
            "decision_complete": False,
        }

    audit_ok = audit.get("autonomy_audit_status") == "passed"
    dv_valid = decision_validation.get("decision_validation_status") == "valid"

    if audit_ok and dv_valid:
        return {
            "autonomy_report_status": "complete",
            "report_phase": phase_id,
            "audit_ok_count": int(audit.get("ok_count", 0)),
            "decision_complete": bool(decision_validation.get("decision_complete", False)),
        }

    return {
        "autonomy_report_status": "incomplete",
        "report_phase": None,
        "audit_ok_count": 0,
        "decision_complete": False,
    }
