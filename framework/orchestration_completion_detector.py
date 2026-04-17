from typing import Any


def detect_workflow_completion(
    plan: dict[str, Any],
    completed_job_ids: list[str],
    failed_job_ids: list[str],
) -> dict[str, Any]:
    if (
        not isinstance(plan, dict)
        or not isinstance(completed_job_ids, list)
        or not isinstance(failed_job_ids, list)
    ):
        return {
            "detection_valid": False,
            "is_complete": False,
            "is_failed": False,
            "completion_type": "invalid_input",
            "unfinished_job_ids": [],
        }

    stages = plan.get("stages", [])
    total_jobs = int(plan.get("total_jobs", 0))

    if not isinstance(stages, list):
        return {
            "detection_valid": False,
            "is_complete": False,
            "is_failed": False,
            "completion_type": "invalid_input",
            "unfinished_job_ids": [],
        }

    all_job_ids = []
    for stage in stages:
        if isinstance(stage, dict):
            job_ids = stage.get("job_ids", [])
            if isinstance(job_ids, list):
                all_job_ids.extend(job_ids)

    unfinished = [
        job_id
        for job_id in all_job_ids
        if job_id not in completed_job_ids and job_id not in failed_job_ids
    ]

    if total_jobs > 0 and len(completed_job_ids) == total_jobs:
        return {
            "detection_valid": True,
            "is_complete": True,
            "is_failed": False,
            "completion_type": "success",
            "unfinished_job_ids": [],
        }

    if (
        len(failed_job_ids) > 0
        and len(completed_job_ids) + len(failed_job_ids) == total_jobs
    ):
        completion_type = (
            "partial_failure" if len(completed_job_ids) > 0 else "full_failure"
        )
        return {
            "detection_valid": True,
            "is_complete": True,
            "is_failed": True,
            "completion_type": completion_type,
            "unfinished_job_ids": [],
        }

    return {
        "detection_valid": True,
        "is_complete": False,
        "is_failed": False,
        "completion_type": "in_progress",
        "unfinished_job_ids": unfinished,
    }


def summarize_completion_detection(result: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(result, dict):
        return {
            "summary_valid": False,
            "is_complete": False,
            "completion_type": "invalid_input",
        }

    return {
        "summary_valid": bool(result.get("detection_valid", False)),
        "is_complete": bool(result.get("is_complete", False)),
        "completion_type": result.get("completion_type", "invalid_input"),
    }
