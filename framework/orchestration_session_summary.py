from typing import Any


def build_session_summary(
    plan: dict[str, Any],
    report_result: dict[str, Any],
    trail_result: dict[str, Any],
    health_result: dict[str, Any],
    alert_result: dict[str, Any],
    archive_result: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(plan, dict)
        or not isinstance(report_result, dict)
        or not isinstance(trail_result, dict)
        or not isinstance(health_result, dict)
        or not isinstance(alert_result, dict)
        or not isinstance(archive_result, dict)
    ):
        return {
            "summary_valid": False,
            "plan_id": "unknown",
            "total_jobs": 0,
            "completed_count": 0,
            "failed_count": 0,
            "elapsed_seconds": 0.0,
            "event_count": 0,
            "health_status": "unknown",
            "alert_count": 0,
            "archive_status": "unknown",
            "session_outcome": "invalid_input",
        }

    total_jobs = int(plan.get("total_jobs", 0))
    completed_count = int(report_result.get("completed_count", 0))
    failed_count = int(report_result.get("failed_count", 0))
    archive_status = archive_result.get("archive_status", "unknown")

    if archive_status != "archived":
        outcome = "unarchived"
    elif report_result.get("report_status") == "complete" and failed_count == 0:
        outcome = "success"
    elif completed_count > 0 and failed_count > 0:
        outcome = "partial"
    elif completed_count == 0 and total_jobs > 0:
        outcome = "failed"
    else:
        outcome = "partial"

    return {
        "summary_valid": True,
        "plan_id": plan.get("plan_id", "unknown"),
        "total_jobs": total_jobs,
        "completed_count": completed_count,
        "failed_count": failed_count,
        "elapsed_seconds": float(report_result.get("elapsed_seconds", 0.0)),
        "event_count": int(trail_result.get("event_count", 0)),
        "health_status": health_result.get("health_status", "unknown"),
        "alert_count": int(alert_result.get("alert_count", 0)),
        "archive_status": archive_status,
        "session_outcome": outcome,
    }


def summarize_session(result: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(result, dict) or result.get("summary_valid") is not True:
        return {
            "summary_valid": False,
            "session_outcome": "invalid_input",
            "completed_count": 0,
            "alert_count": 0,
        }

    return {
        "summary_valid": True,
        "session_outcome": result.get("session_outcome", "invalid_input"),
        "completed_count": int(result.get("completed_count", 0)),
        "alert_count": int(result.get("alert_count", 0)),
    }
