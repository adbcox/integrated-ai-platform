from typing import Any


def report_critique(
    critique_auditor: dict[str, Any],
    counterfactual_critique: dict[str, Any],
    phase_id: str,
) -> dict[str, Any]:
    if (
        not isinstance(critique_auditor, dict)
        or not isinstance(counterfactual_critique, dict)
        or not isinstance(phase_id, str)
    ):
        return {
            "critique_report_status": "invalid_input",
            "report_phase": None,
            "report_detail": None,
        }

    ca_ok = critique_auditor.get("critique_audit_status") == "passed"
    cc_ok = counterfactual_critique.get("cf_critique_status") == "synthesized"
    all_ok = ca_ok and cc_ok

    if all_ok:
        return {
            "critique_report_status": "complete",
            "report_phase": phase_id,
            "report_detail": "critique_reported",
        }

    return {
        "critique_report_status": "incomplete",
        "report_phase": None,
        "report_detail": None,
    }
