from typing import Any


def write_workflow_archive(
    finalization_result: dict[str, Any],
    checkpoint: dict[str, Any],
    trail_result: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(finalization_result, dict)
        or not isinstance(checkpoint, dict)
        or not isinstance(trail_result, dict)
    ):
        return {
            "archive_valid": False,
            "plan_id": "unknown",
            "total_jobs": 0,
            "finalization_status": "unknown",
            "checkpoint_status": "unknown",
            "trail_status": "unknown",
            "event_count": 0,
            "archive_status": "invalid_input",
        }

    archive_status = (
        "archived"
        if finalization_result.get("finalization_status") == "finalized"
        and checkpoint.get("checkpoint_status") == "written"
        else "rejected"
    )

    return {
        "archive_valid": True,
        "plan_id": finalization_result.get("plan_id", "unknown"),
        "total_jobs": int(finalization_result.get("total_jobs", 0)),
        "finalization_status": finalization_result.get(
            "finalization_status", "unknown"
        ),
        "checkpoint_status": checkpoint.get("checkpoint_status", "unknown"),
        "trail_status": trail_result.get("trail_status", "unknown"),
        "event_count": int(trail_result.get("event_count", 0)),
        "archive_status": archive_status,
    }


def summarize_archive(result: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(result, dict) or result.get("archive_valid") is not True:
        return {
            "summary_valid": False,
            "archive_status": "invalid_input",
            "plan_id": "unknown",
        }

    return {
        "summary_valid": True,
        "archive_status": result.get("archive_status", "invalid_input"),
        "plan_id": result.get("plan_id", "unknown"),
    }
