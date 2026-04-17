from typing import Any


def validate_restoration_consistency(
    original_archive_result: dict[str, Any],
    restored_checkpoint_result: dict[str, Any],
    restored_trail_result: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(original_archive_result, dict)
        or not isinstance(restored_checkpoint_result, dict)
        or not isinstance(restored_trail_result, dict)
    ):
        return {
            "validation_valid": False,
            "plan_id_match": False,
            "total_jobs_match": False,
            "trail_event_count_nonzero": False,
            "restoration_consistent": False,
            "restoration_status": "invalid_input",
        }

    original_plan_id = original_archive_result.get("plan_id", "unknown")
    restored_plan_id = restored_checkpoint_result.get("plan_id", "unknown")
    plan_id_match = original_plan_id == restored_plan_id

    original_total_jobs = int(original_archive_result.get("total_jobs", 0))
    restored_total_jobs = int(restored_checkpoint_result.get("total_jobs", 0))
    total_jobs_match = original_total_jobs == restored_total_jobs

    trail_events = restored_trail_result.get("events", [])
    trail_event_count = len(trail_events) if isinstance(trail_events, list) else 0
    trail_event_count_nonzero = trail_event_count > 0

    restoration_consistent = plan_id_match and total_jobs_match and trail_event_count_nonzero

    if restoration_consistent:
        status = "consistent"
    elif plan_id_match and total_jobs_match:
        status = "partial_consistency"
    else:
        status = "inconsistent"

    return {
        "validation_valid": True,
        "plan_id_match": plan_id_match,
        "total_jobs_match": total_jobs_match,
        "trail_event_count_nonzero": trail_event_count_nonzero,
        "restoration_consistent": restoration_consistent,
        "restoration_status": status,
    }


def summarize_restoration_validation(result: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(result, dict) or result.get("validation_valid") is not True:
        return {
            "summary_valid": False,
            "restoration_status": "invalid_input",
            "restoration_consistent": False,
        }

    return {
        "summary_valid": True,
        "restoration_status": result.get("restoration_status", "invalid_input"),
        "restoration_consistent": bool(result.get("restoration_consistent", False)),
    }
