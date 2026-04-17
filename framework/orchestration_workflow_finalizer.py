from typing import Any


def finalize_workflow(
    plan: dict[str, Any],
    completion_result: dict[str, Any],
    report_result: dict[str, Any],
    trail_result: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(plan, dict)
        or not isinstance(completion_result, dict)
        or not isinstance(report_result, dict)
        or not isinstance(trail_result, dict)
    ):
        return {
            "finalization_valid": False,
            "plan_id": "unknown",
            "total_jobs": 0,
            "completion_type": "unknown",
            "report_status": "unknown",
            "trail_status": "unknown",
            "elapsed_seconds": 0.0,
            "finalization_status": "invalid_input",
        }

    is_complete = completion_result.get("is_complete", False) is True
    report_status = report_result.get("report_status", "unknown")

    status = (
        "finalized"
        if is_complete and report_status == "complete"
        else "incomplete"
    )

    return {
        "finalization_valid": True,
        "plan_id": plan.get("plan_id", "unknown"),
        "total_jobs": int(plan.get("total_jobs", 0)),
        "completion_type": completion_result.get("completion_type", "unknown"),
        "report_status": report_status,
        "trail_status": trail_result.get("trail_status", "unknown"),
        "elapsed_seconds": float(report_result.get("elapsed_seconds", 0.0)),
        "finalization_status": status,
    }


def summarize_finalization(result: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(result, dict) or result.get("finalization_valid") is not True:
        return {
            "summary_valid": False,
            "finalization_status": "invalid_input",
            "completion_type": "unknown",
        }

    return {
        "summary_valid": True,
        "finalization_status": result.get("finalization_status", "invalid_input"),
        "completion_type": result.get("completion_type", "unknown"),
    }
