from typing import Any


def build_operator_handoff(
    final_report_result: dict[str, Any],
    transition_result: dict[str, Any],
    closure_result: dict[str, Any],
    operational_status_result: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(final_report_result, dict)
        or not isinstance(transition_result, dict)
        or not isinstance(closure_result, dict)
        or not isinstance(operational_status_result, dict)
    ):
        return {
            "handoff_valid": False,
            "report_approved": False,
            "transition_approved": False,
            "closure_approved": False,
            "operational_approved": False,
            "handoff_complete": False,
            "handoff_conditions": [],
            "handoff_status": "invalid_input",
        }

    report_approved = final_report_result.get("final_report_status") == "signed_off"
    transition_approved = transition_result.get("transition_recommendation") == "proceed"
    closure_approved = closure_result.get("closure_status") == "closed"
    operational_approved = operational_status_result.get("overall_operational_status") == "operational"

    conditions = []
    if not report_approved:
        conditions.append("report_approved")
    if not transition_approved:
        conditions.append("transition_approved")
    if not closure_approved:
        conditions.append("closure_approved")
    if not operational_approved:
        conditions.append("operational_approved")

    handoff_complete = len(conditions) == 0

    if handoff_complete:
        status = "approved"
    elif len(conditions) <= 2:
        status = "pending"
    else:
        status = "blocked"

    return {
        "handoff_valid": True,
        "report_approved": report_approved,
        "transition_approved": transition_approved,
        "closure_approved": closure_approved,
        "operational_approved": operational_approved,
        "handoff_complete": handoff_complete,
        "handoff_conditions": conditions,
        "handoff_status": status,
    }


def summarize_operator_handoff(result: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(result, dict) or result.get("handoff_valid") is not True:
        return {
            "summary_valid": False,
            "handoff_status": "invalid_input",
            "handoff_complete": False,
            "condition_count": 0,
        }

    return {
        "summary_valid": True,
        "handoff_status": result.get("handoff_status", "invalid_input"),
        "handoff_complete": bool(result.get("handoff_complete", False)),
        "condition_count": (
            len(result.get("handoff_conditions", []))
            if isinstance(result.get("handoff_conditions", []), list)
            else 0
        ),
    }
