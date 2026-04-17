from typing import Any


def generate_final_phase_report(
    multi_reconcile_result: dict[str, Any],
    audit_result: dict[str, Any],
    closure_result: dict[str, Any],
    transition_result: dict[str, Any],
    telemetry_aggregation: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(multi_reconcile_result, dict)
        or not isinstance(audit_result, dict)
        or not isinstance(closure_result, dict)
        or not isinstance(transition_result, dict)
        or not isinstance(telemetry_aggregation, dict)
    ):
        return {
            "report_valid": False,
            "workflow_count": 0,
            "success_count": 0,
            "audit_status": "unknown",
            "closure_status": "unknown",
            "transition_recommendation": "unknown",
            "total_telemetry_records": 0,
            "phase_sign_off": False,
            "final_report_status": "invalid_input",
        }

    audit_status = audit_result.get("audit_status", "unknown")
    closure_status = closure_result.get("closure_status", "unknown")
    transition_recommendation = transition_result.get(
        "transition_recommendation", "unknown"
    )

    phase_sign_off = (
        audit_status == "passed"
        and closure_status == "closed"
        and transition_recommendation == "proceed"
        and multi_reconcile_result.get("divergence_detected", True) is False
    )

    if phase_sign_off:
        status = "signed_off"
    elif transition_recommendation in ("investigate",) or audit_status in ("failed",):
        status = "blocked"
    else:
        status = "pending"

    return {
        "report_valid": True,
        "workflow_count": int(multi_reconcile_result.get("workflow_count", 0)),
        "success_count": int(multi_reconcile_result.get("success_count", 0)),
        "audit_status": audit_status,
        "closure_status": closure_status,
        "transition_recommendation": transition_recommendation,
        "total_telemetry_records": int(
            telemetry_aggregation.get("total_record_count", 0)
        ),
        "phase_sign_off": phase_sign_off,
        "final_report_status": status,
    }


def summarize_final_phase_report(result: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(result, dict) or result.get("report_valid") is not True:
        return {
            "summary_valid": False,
            "final_report_status": "invalid_input",
            "phase_sign_off": False,
            "workflow_count": 0,
        }

    return {
        "summary_valid": True,
        "final_report_status": result.get("final_report_status", "invalid_input"),
        "phase_sign_off": bool(result.get("phase_sign_off", False)),
        "workflow_count": int(result.get("workflow_count", 0)),
    }
