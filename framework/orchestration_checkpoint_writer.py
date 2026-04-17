from typing import Any


def write_workflow_checkpoint(
    plan: dict[str, Any],
    completed_job_ids: list[str],
    failed_job_ids: list[str],
    active_stage_index: int,
    elapsed_seconds: float,
) -> dict[str, Any]:
    if (
        not isinstance(plan, dict)
        or not plan.get("plan_valid", False)
        or not isinstance(completed_job_ids, list)
        or not isinstance(failed_job_ids, list)
    ):
        return {
            "checkpoint_valid": False,
            "plan_id": "unknown",
            "completed_job_ids": [],
            "failed_job_ids": [],
            "active_stage_index": 0,
            "elapsed_seconds": 0.0,
            "total_jobs": 0,
            "snapshot_valid": False,
            "checkpoint_status": "invalid_input",
        }

    return {
        "checkpoint_valid": True,
        "plan_id": plan.get("plan_id", "unknown"),
        "completed_job_ids": list(completed_job_ids),
        "failed_job_ids": list(failed_job_ids),
        "active_stage_index": max(0, int(active_stage_index)),
        "elapsed_seconds": max(0.0, float(elapsed_seconds)),
        "total_jobs": int(plan.get("total_jobs", 0)),
        "snapshot_valid": True,
        "checkpoint_status": "written",
    }


def summarize_checkpoint(result: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(result, dict) or result.get("checkpoint_valid") is not True:
        return {
            "summary_valid": False,
            "checkpoint_status": "invalid_input",
            "completed_count": 0,
            "failed_count": 0,
        }

    return {
        "summary_valid": True,
        "checkpoint_status": result.get("checkpoint_status", "invalid_input"),
        "completed_count": (
            len(result.get("completed_job_ids", []))
            if isinstance(result.get("completed_job_ids", []), list)
            else 0
        ),
        "failed_count": (
            len(result.get("failed_job_ids", []))
            if isinstance(result.get("failed_job_ids", []), list)
            else 0
        ),
    }
