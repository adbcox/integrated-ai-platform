from typing import Any


def aggregate_workflow_progress(
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
            "aggregation_valid": False,
            "total_jobs": 0,
            "completed_count": 0,
            "failed_count": 0,
            "pending_count": 0,
            "progress_pct": 0.0,
            "stages_completed": 0,
            "stages_total": 0,
        }

    stages = plan.get("stages", [])
    total_jobs = int(plan.get("total_jobs", 0))

    if not isinstance(stages, list):
        return {
            "aggregation_valid": False,
            "total_jobs": 0,
            "completed_count": 0,
            "failed_count": 0,
            "pending_count": 0,
            "progress_pct": 0.0,
            "stages_completed": 0,
            "stages_total": 0,
        }

    completed_count = len(completed_job_ids)
    failed_count = len(failed_job_ids)
    pending_count = max(0, total_jobs - completed_count - failed_count)

    progress_pct = (
        round((completed_count / float(total_jobs)) * 100.0, 3)
        if total_jobs > 0
        else 0.0
    )

    stages_completed = 0
    for stage in stages:
        if not isinstance(stage, dict):
            continue
        job_ids = stage.get("job_ids", [])
        if (
            isinstance(job_ids, list)
            and job_ids
            and all(job_id in completed_job_ids for job_id in job_ids)
        ):
            stages_completed += 1

    return {
        "aggregation_valid": True,
        "total_jobs": total_jobs,
        "completed_count": completed_count,
        "failed_count": failed_count,
        "pending_count": pending_count,
        "progress_pct": progress_pct,
        "stages_completed": stages_completed,
        "stages_total": len(stages),
    }


def summarize_progress_aggregation(result: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(result, dict):
        return {
            "summary_valid": False,
            "progress_pct": 0.0,
            "stages_completed": 0,
            "stages_total": 0,
        }

    return {
        "summary_valid": bool(result.get("aggregation_valid", False)),
        "progress_pct": float(result.get("progress_pct", 0.0)),
        "stages_completed": int(result.get("stages_completed", 0)),
        "stages_total": int(result.get("stages_total", 0)),
    }
