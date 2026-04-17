from typing import Any


def validate_checkpoint(
    checkpoint: dict[str, Any],
    plan: dict[str, Any],
) -> dict[str, Any]:
    if not isinstance(checkpoint, dict) or not isinstance(plan, dict):
        return {
            "validation_valid": False,
            "fields_present": False,
            "plan_consistent": False,
            "jobs_within_plan": False,
            "active_stage_in_range": False,
            "validation_status": "invalid_input",
            "validation_errors": [],
        }

    required_fields = [
        "checkpoint_valid",
        "completed_job_ids",
        "failed_job_ids",
        "active_stage_index",
        "snapshot_valid",
        "total_jobs",
    ]
    fields_present = all(field in checkpoint for field in required_fields)

    stages = plan.get("stages", [])
    if not isinstance(stages, list):
        stages = []

    plan_job_ids = []
    for stage in stages:
        if isinstance(stage, dict):
            job_ids = stage.get("job_ids", [])
            if isinstance(job_ids, list):
                plan_job_ids.extend(job_ids)

    completed_job_ids = checkpoint.get("completed_job_ids", [])
    failed_job_ids = checkpoint.get("failed_job_ids", [])

    if not isinstance(completed_job_ids, list):
        completed_job_ids = []
    if not isinstance(failed_job_ids, list):
        failed_job_ids = []

    jobs_within_plan = all(
        job_id in plan_job_ids for job_id in completed_job_ids + failed_job_ids
    )

    active_stage_in_range = int(checkpoint.get("active_stage_index", -1)) < len(
        stages
    )

    plan_consistent = checkpoint.get("plan_id", "unknown") == plan.get(
        "plan_id", "unknown"
    )

    validation_errors = []
    if not fields_present:
        validation_errors.append("fields_present")
    if not plan_consistent:
        validation_errors.append("plan_consistent")
    if not jobs_within_plan:
        validation_errors.append("jobs_within_plan")
    if not active_stage_in_range:
        validation_errors.append("active_stage_in_range")

    if len(validation_errors) == 0:
        status = "valid"
    elif len(validation_errors) <= 2:
        status = "partial"
    else:
        status = "invalid"

    return {
        "validation_valid": True,
        "fields_present": fields_present,
        "plan_consistent": plan_consistent,
        "jobs_within_plan": jobs_within_plan,
        "active_stage_in_range": active_stage_in_range,
        "validation_status": status,
        "validation_errors": validation_errors,
    }


def summarize_checkpoint_validation(result: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(result, dict) or result.get("validation_valid") is not True:
        return {
            "summary_valid": False,
            "validation_status": "invalid_input",
            "error_count": 0,
        }

    return {
        "summary_valid": True,
        "validation_status": result.get("validation_status", "invalid_input"),
        "error_count": (
            len(result.get("validation_errors", []))
            if isinstance(result.get("validation_errors", []), list)
            else 0
        ),
    }
