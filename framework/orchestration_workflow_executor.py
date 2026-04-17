from typing import Any


def advance_workflow_execution(
    plan: dict[str, Any],
    current_state: dict[str, Any],
) -> dict[str, Any]:
    if not isinstance(plan, dict) or not isinstance(current_state, dict):
        return {
            "advance_valid": False,
            "next_stage_index": -1,
            "jobs_ready_to_run": [],
            "advance_status": "invalid_input",
        }

    stages = plan.get("stages", [])
    total_jobs = int(plan.get("total_jobs", 0))
    completed_job_ids = current_state.get("completed_job_ids", [])
    failed_job_ids = current_state.get("failed_job_ids", [])
    active_stage_index = current_state.get("active_stage_index", 0)

    if (
        not isinstance(stages, list)
        or not isinstance(completed_job_ids, list)
        or not isinstance(failed_job_ids, list)
        or not isinstance(active_stage_index, int)
    ):
        return {
            "advance_valid": False,
            "next_stage_index": -1,
            "jobs_ready_to_run": [],
            "advance_status": "invalid_input",
        }

    if total_jobs > 0 and len(completed_job_ids) >= total_jobs:
        return {
            "advance_valid": True,
            "next_stage_index": active_stage_index,
            "jobs_ready_to_run": [],
            "advance_status": "complete",
        }

    if active_stage_index < 0 or active_stage_index >= len(stages):
        return {
            "advance_valid": False,
            "next_stage_index": -1,
            "jobs_ready_to_run": [],
            "advance_status": "invalid_input",
        }

    stage = stages[active_stage_index]
    if not isinstance(stage, dict):
        return {
            "advance_valid": False,
            "next_stage_index": -1,
            "jobs_ready_to_run": [],
            "advance_status": "invalid_input",
        }

    job_ids = stage.get("job_ids", [])
    dependencies = stage.get("dependencies", [])

    if not isinstance(job_ids, list) or not isinstance(dependencies, list):
        return {
            "advance_valid": False,
            "next_stage_index": -1,
            "jobs_ready_to_run": [],
            "advance_status": "invalid_input",
        }

    if any(job_id in failed_job_ids for job_id in job_ids):
        return {
            "advance_valid": True,
            "next_stage_index": active_stage_index,
            "jobs_ready_to_run": [],
            "advance_status": "blocked",
        }

    jobs_ready = []
    for job_id in job_ids:
        if job_id in completed_job_ids:
            continue
        if all(dep in completed_job_ids for dep in dependencies):
            jobs_ready.append(job_id)

    if jobs_ready:
        return {
            "advance_valid": True,
            "next_stage_index": active_stage_index,
            "jobs_ready_to_run": jobs_ready,
            "advance_status": "advanced",
        }

    return {
        "advance_valid": True,
        "next_stage_index": active_stage_index,
        "jobs_ready_to_run": [],
        "advance_status": "waiting",
    }


def summarize_workflow_advance(result: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(result, dict):
        return {
            "summary_valid": False,
            "jobs_ready": 0,
            "advance_status": "invalid_input",
        }

    return {
        "summary_valid": bool(result.get("advance_valid", False)),
        "jobs_ready": (
            len(result.get("jobs_ready_to_run", []))
            if isinstance(result.get("jobs_ready_to_run", []), list)
            else 0
        ),
        "advance_status": result.get("advance_status", "invalid_input"),
    }
