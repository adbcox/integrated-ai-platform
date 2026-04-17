from typing import Any


def plan_workflow_replay(
    readiness_result: dict[str, Any],
    archive_result: dict[str, Any],
    checkpoint_result: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(readiness_result, dict)
        or not isinstance(archive_result, dict)
        or not isinstance(checkpoint_result, dict)
    ):
        return {
            "plan_valid": False,
            "plan_id": "unknown",
            "total_jobs": 0,
            "replay_start_index": 0,
            "jobs_to_replay": [],
            "replay_mode": "unknown",
            "replay_plan_status": "invalid_input",
        }

    if readiness_result.get("replay_ready") is not True:
        return {
            "plan_valid": False,
            "plan_id": "unknown",
            "total_jobs": 0,
            "replay_start_index": 0,
            "jobs_to_replay": [],
            "replay_mode": "unknown",
            "replay_plan_status": "invalid_input",
        }

    plan_id = archive_result.get("plan_id", "unknown")
    total_jobs = int(archive_result.get("total_jobs", 0))
    replay_start_index = int(checkpoint_result.get("active_stage_index", 0))
    completed_job_ids = checkpoint_result.get("completed_job_ids", [])
    failed_job_ids = checkpoint_result.get("failed_job_ids", [])

    if not isinstance(completed_job_ids, list):
        completed_job_ids = []
    if not isinstance(failed_job_ids, list):
        failed_job_ids = []

    synthetic_ids = ["job-{}".format(i) for i in range(1, total_jobs + 1)]
    jobs_to_replay = [j for j in synthetic_ids if j not in completed_job_ids]
    replay_mode = "full" if len(completed_job_ids) == 0 else "partial"
    status = "nothing_to_replay" if len(jobs_to_replay) == 0 else "planned"

    return {
        "plan_valid": True,
        "plan_id": plan_id,
        "total_jobs": total_jobs,
        "replay_start_index": replay_start_index,
        "jobs_to_replay": jobs_to_replay,
        "replay_mode": replay_mode,
        "replay_plan_status": status,
    }


def summarize_replay_plan(result: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(result, dict) or result.get("plan_valid") is not True:
        return {
            "summary_valid": False,
            "replay_plan_status": "invalid_input",
            "replay_mode": "unknown",
            "jobs_to_replay_count": 0,
        }

    return {
        "summary_valid": True,
        "replay_plan_status": result.get("replay_plan_status", "invalid_input"),
        "replay_mode": result.get("replay_mode", "unknown"),
        "jobs_to_replay_count": (
            len(result.get("jobs_to_replay", []))
            if isinstance(result.get("jobs_to_replay", []), list)
            else 0
        ),
    }
