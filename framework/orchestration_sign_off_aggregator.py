from typing import Any


def aggregate_sign_offs(
    final_report_result: dict[str, Any],
    handoff_result: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(final_report_result, dict)
        or not isinstance(handoff_result, dict)
    ):
        return {
            "aggregation_valid": False,
            "report_sign_off": False,
            "handoff_approved": False,
            "release_gate_passed": False,
            "sign_off_count": 0,
            "approval_count": 0,
            "aggregation_status": "invalid_input",
        }

    report_sign_off = final_report_result.get("phase_sign_off") is True
    handoff_approved = handoff_result.get("handoff_status") == "approved"

    sign_off_count = 1 if report_sign_off else 0
    approval_count = 1 if handoff_approved else 0

    sign_off_rate = round((sign_off_count / 1.0) * 100.0, 1) if sign_off_count > 0 else 0.0
    approval_rate = round((approval_count / 1.0) * 100.0, 1) if approval_count > 0 else 0.0

    release_gate_passed = (sign_off_rate == 100.0) and (approval_rate == 100.0)

    if release_gate_passed:
        status = "all_approved"
    elif sign_off_rate == 100.0 or approval_rate == 100.0:
        status = "partial_approval"
    else:
        status = "pending_approval"

    return {
        "aggregation_valid": True,
        "report_sign_off": report_sign_off,
        "handoff_approved": handoff_approved,
        "release_gate_passed": release_gate_passed,
        "sign_off_count": sign_off_count,
        "approval_count": approval_count,
        "aggregation_status": status,
    }


def summarize_sign_off_aggregation(result: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(result, dict) or result.get("aggregation_valid") is not True:
        return {
            "summary_valid": False,
            "aggregation_status": "invalid_input",
            "release_gate_passed": False,
        }

    return {
        "summary_valid": True,
        "aggregation_status": result.get("aggregation_status", "invalid_input"),
        "release_gate_passed": bool(result.get("release_gate_passed", False)),
    }
