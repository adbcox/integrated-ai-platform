from typing import Any

def coordinate_job_dispatch(
    job_id: str,
    job_priority: str,
    job_queue: list[dict[str, Any]],
) -> dict[str, Any]:
    if not isinstance(job_queue, list):
        job_queue = []
    priority_rank = {"p0": 0, "p1": 1, "p2": 2, "p3": 3}.get(job_priority, 2)
    dispatch_timing = "immediate" if priority_rank <= 1 else "queued"
    dispatch_position = len([j for j in job_queue if isinstance(j, dict) and j.get("priority", "p3") >= job_priority])
    return {
        "job_id": job_id,
        "dispatch_timing": dispatch_timing,
        "dispatch_position": dispatch_position,
        "dispatch_target": "local_executor",
        "dispatch_plan_status": "ready",
    }
