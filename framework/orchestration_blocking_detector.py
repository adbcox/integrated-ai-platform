from typing import Any


def detect_blocking_conditions(
    plan: dict[str, Any],
    current_state: dict[str, Any],
    elapsed_seconds: float,
    stall_threshold_seconds: float,
) -> dict[str, Any]:
    if (
        not isinstance(plan, dict)
        or not isinstance(current_state, dict)
        or not plan.get("plan_valid", False)
    ):
        return {
            "detection_valid": False,
            "is_stalled": False,
            "is_deadlocked": False,
            "blocking_job_ids": [],
            "blocking_type": "invalid_input",
        }

    stages = plan.get("stages", [])
    if not isinstance(stages, list):
        return {
            "detection_valid": False,
            "is_stalled": False,
            "is_deadlocked": False,
            "blocking_job_ids": [],
            "blocking_type": "invalid_input",
        }

    completed_job_ids = current_state.get("completed_job_ids", [])
    failed_job_ids = current_state.get("failed_job_ids", [])
    active_stage_index = current_state.get("active_stage_index", 0)
    last_progress_seconds = float(current_state.get("last_progress_seconds", 0.0))

    if (
        not isinstance(completed_job_ids, list)
        or not isinstance(failed_job_ids, list)
        or not isinstance(active_stage_index, int)
    ):
        return {
            "detection_valid": False,
            "is_stalled": False,
            "is_deadlocked": False,
            "blocking_job_ids": [],
            "blocking_type": "invalid_input",
        }

    is_stalled = (elapsed_seconds - last_progress_seconds) > stall_threshold_seconds

    if 0 <= active_stage_index < len(stages) and isinstance(
        stages[active_stage_index], dict
    ):
        stage_job_ids = stages[active_stage_index].get("job_ids", [])
        if not isinstance(stage_job_ids, list):
            stage_job_ids = []
    else:
        stage_job_ids = []

    blocking_job_ids = sorted(
        [
            job_id
            for job_id in stage_job_ids
            if job_id not in completed_job_ids and job_id not in failed_job_ids
        ]
    )

    is_deadlocked = is_stalled and len(blocking_job_ids) > 0

    if is_deadlocked:
        blocking_type = "deadlock"
    elif is_stalled:
        blocking_type = "stall"
    else:
        blocking_type = "none"

    return {
        "detection_valid": True,
        "is_stalled": is_stalled,
        "is_deadlocked": is_deadlocked,
        "blocking_job_ids": blocking_job_ids,
        "blocking_type": blocking_type,
    }


def summarize_blocking_detection(result: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(result, dict) or result.get("detection_valid") is not True:
        return {
            "summary_valid": False,
            "blocking_type": "invalid_input",
            "blocking_job_count": 0,
        }

    return {
        "summary_valid": True,
        "blocking_type": result.get("blocking_type", "invalid_input"),
        "blocking_job_count": (
            len(result.get("blocking_job_ids", []))
            if isinstance(result.get("blocking_job_ids", []), list)
            else 0
        ),
    }
