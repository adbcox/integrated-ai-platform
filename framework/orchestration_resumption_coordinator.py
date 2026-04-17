from typing import Any


def coordinate_resumption(
    plan: dict[str, Any],
    checkpoint: dict[str, Any],
    retry_policy: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(plan, dict)
        or not isinstance(checkpoint, dict)
        or not isinstance(retry_policy, dict)
        or not plan.get("plan_valid", False)
    ):
        return {
            "coordination_valid": False,
            "reconciled_completed": [],
            "reconciled_failed": [],
            "active_stage_index": 0,
            "retry_candidates": [],
            "jobs_pending": [],
            "resumption_action": "invalid_input",
        }

    stages = plan.get("stages", [])
    if not isinstance(stages, list):
        stages = []

    plan_job_ids = []
    for stage in stages:
        if isinstance(stage, dict):
            job_ids = stage.get("job_ids", [])
            if isinstance(job_ids, list):
                plan_job_ids.extend(job_ids)

    completed = checkpoint.get("completed_job_ids", [])
    failed = checkpoint.get("failed_job_ids", [])

    if not isinstance(completed, list):
        completed = []
    if not isinstance(failed, list):
        failed = []

    reconciled_completed = sorted(
        [job_id for job_id in completed if job_id in plan_job_ids]
    )
    reconciled_failed = sorted(
        [job_id for job_id in failed if job_id in plan_job_ids]
    )

    jobs_pending = sorted(
        [
            job_id
            for job_id in plan_job_ids
            if job_id not in reconciled_completed and job_id not in reconciled_failed
        ]
    )

    max_attempts = int(retry_policy.get("max_attempts", 0))
    retry_candidates = sorted(reconciled_failed) if max_attempts >= 1 else []

    if not jobs_pending and not reconciled_failed:
        action = "complete"
    elif not jobs_pending and reconciled_failed and not retry_candidates:
        action = "unrecoverable"
    elif retry_candidates:
        action = "retry_and_resume"
    else:
        action = "resume"

    return {
        "coordination_valid": True,
        "reconciled_completed": reconciled_completed,
        "reconciled_failed": reconciled_failed,
        "active_stage_index": int(checkpoint.get("active_stage_index", 0)),
        "retry_candidates": retry_candidates,
        "jobs_pending": jobs_pending,
        "resumption_action": action,
    }


def summarize_resumption(result: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(result, dict) or result.get("coordination_valid") is not True:
        return {
            "summary_valid": False,
            "resumption_action": "invalid_input",
            "jobs_pending": 0,
            "retry_candidates": 0,
        }

    return {
        "summary_valid": True,
        "resumption_action": result.get("resumption_action", "invalid_input"),
        "jobs_pending": (
            len(result.get("jobs_pending", []))
            if isinstance(result.get("jobs_pending", []), list)
            else 0
        ),
        "retry_candidates": (
            len(result.get("retry_candidates", []))
            if isinstance(result.get("retry_candidates", []), list)
            else 0
        ),
    }
