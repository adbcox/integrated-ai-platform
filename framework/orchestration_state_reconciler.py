from typing import Any


def reconcile_workflow_state(
    plan: dict[str, Any],
    persisted_snapshot: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(plan, dict)
        or not isinstance(persisted_snapshot, dict)
        or not plan.get("plan_valid", False)
    ):
        return {
            "reconcile_valid": False,
            "reconciled_completed": [],
            "reconciled_failed": [],
            "active_stage_index": 0,
            "orphaned_job_ids": [],
            "reconcile_status": "invalid_input",
        }

    if persisted_snapshot.get("snapshot_valid") is False:
        return {
            "reconcile_valid": True,
            "reconciled_completed": [],
            "reconciled_failed": [],
            "active_stage_index": 0,
            "orphaned_job_ids": [],
            "reconcile_status": "clean",
        }

    stages = plan.get("stages", [])
    if not isinstance(stages, list):
        return {
            "reconcile_valid": False,
            "reconciled_completed": [],
            "reconciled_failed": [],
            "active_stage_index": 0,
            "orphaned_job_ids": [],
            "reconcile_status": "invalid_input",
        }

    plan_job_ids = []
    for stage in stages:
        if isinstance(stage, dict):
            job_ids = stage.get("job_ids", [])
            if isinstance(job_ids, list):
                plan_job_ids.extend(job_ids)

    completed = persisted_snapshot.get("completed_job_ids", [])
    failed = persisted_snapshot.get("failed_job_ids", [])
    active_stage_index = persisted_snapshot.get("active_stage_index", 0)

    if (
        not isinstance(completed, list)
        or not isinstance(failed, list)
        or not isinstance(active_stage_index, int)
    ):
        return {
            "reconcile_valid": False,
            "reconciled_completed": [],
            "reconciled_failed": [],
            "active_stage_index": 0,
            "orphaned_job_ids": [],
            "reconcile_status": "invalid_input",
        }

    reconciled_completed = sorted(
        [job_id for job_id in completed if job_id in plan_job_ids]
    )
    reconciled_failed = sorted(
        [job_id for job_id in failed if job_id in plan_job_ids]
    )
    orphaned = sorted(
        [job_id for job_id in completed + failed if job_id not in plan_job_ids]
    )

    if len(stages) == 0:
        clamped_stage_index = 0
    else:
        clamped_stage_index = min(max(active_stage_index, 0), len(stages) - 1)

    if orphaned:
        status = "orphaned"
    elif reconciled_failed:
        status = "partial"
    else:
        status = "clean"

    return {
        "reconcile_valid": True,
        "reconciled_completed": reconciled_completed,
        "reconciled_failed": reconciled_failed,
        "active_stage_index": clamped_stage_index,
        "orphaned_job_ids": orphaned,
        "reconcile_status": status,
    }


def summarize_reconciliation(result: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(result, dict) or result.get("reconcile_valid") is not True:
        return {
            "summary_valid": False,
            "reconcile_status": "invalid_input",
            "orphaned_count": 0,
        }

    return {
        "summary_valid": True,
        "reconcile_status": result.get("reconcile_status", "invalid_input"),
        "orphaned_count": (
            len(result.get("orphaned_job_ids", []))
            if isinstance(result.get("orphaned_job_ids", []), list)
            else 0
        ),
    }
