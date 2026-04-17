from typing import Any


def build_workflow_plan(jobs: list[dict[str, Any]]) -> dict[str, Any]:
    if not isinstance(jobs, list):
        return {
            "plan_valid": False,
            "stages": [],
            "total_jobs": 0,
            "estimated_duration": 0,
        }

    valid_jobs = [
        j for j in jobs if isinstance(j, dict) and j.get("job_id", "")
    ]
    ordered = sorted(
        valid_jobs,
        key=lambda j: (j.get("priority", "p9"), j.get("job_id", "")),
    )

    stage = {
        "stage_id": "stage-1",
        "stage_index": 0,
        "job_ids": [j.get("job_id", "") for j in ordered],
        "dependencies": [],
    }

    estimated_duration = len(ordered) * 10

    return {
        "plan_valid": True,
        "stages": [stage],
        "total_jobs": len(ordered),
        "estimated_duration": estimated_duration,
    }


def summarize_workflow_plan(plan: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(plan, dict):
        return {"summary_valid": False, "stage_count": 0, "job_count": 0}

    stages = plan.get("stages", [])
    total_jobs = plan.get("total_jobs", 0)

    return {
        "summary_valid": True,
        "stage_count": len(stages),
        "job_count": total_jobs,
    }
