from typing import Any


def build_audit_trail(
    plan: dict[str, Any],
    execution_events: list[dict[str, Any]],
) -> dict[str, Any]:
    if (
        not isinstance(plan, dict)
        or not plan.get("plan_valid", False)
        or not isinstance(execution_events, list)
    ):
        return {
            "trail_valid": False,
            "event_count": 0,
            "job_events": {},
            "stage_events": {},
            "escalation_count": 0,
            "completed_via_trail": [],
            "failed_via_trail": [],
            "trail_status": "invalid_input",
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

    if not execution_events:
        return {
            "trail_valid": True,
            "event_count": 0,
            "job_events": {},
            "stage_events": {},
            "escalation_count": 0,
            "completed_via_trail": [],
            "failed_via_trail": [],
            "trail_status": "empty",
        }

    job_events = {}
    stage_events = {}
    escalation_count = 0
    completed_via_trail = set()
    failed_via_trail = set()
    event_count = 0

    for event in execution_events:
        if not isinstance(event, dict) or "event_type" not in event:
            continue

        event_type = event.get("event_type", "")
        job_id = event.get("job_id", "")
        stage_id = event.get("stage_id", "")
        event_count += 1

        if job_id:
            job_events.setdefault(job_id, []).append(event_type)

        if stage_id:
            stage_events.setdefault(stage_id, []).append(event_type)

        if event_type == "escalated":
            escalation_count += 1

        if event_type == "job_completed" and job_id:
            completed_via_trail.add(job_id)

        if event_type == "job_failed" and job_id:
            failed_via_trail.add(job_id)

    covered = sorted(completed_via_trail | failed_via_trail)
    status = (
        "complete"
        if sorted([job_id for job_id in plan_job_ids]) == covered
        else "partial"
    )

    return {
        "trail_valid": True,
        "event_count": event_count,
        "job_events": {k: job_events[k] for k in sorted(job_events.keys())},
        "stage_events": {k: stage_events[k] for k in sorted(stage_events.keys())},
        "escalation_count": escalation_count,
        "completed_via_trail": sorted(completed_via_trail),
        "failed_via_trail": sorted(failed_via_trail),
        "trail_status": status,
    }


def summarize_audit_trail(result: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(result, dict) or result.get("trail_valid") is not True:
        return {
            "summary_valid": False,
            "trail_status": "invalid_input",
            "event_count": 0,
            "escalation_count": 0,
        }

    return {
        "summary_valid": True,
        "trail_status": result.get("trail_status", "invalid_input"),
        "event_count": int(result.get("event_count", 0)),
        "escalation_count": int(result.get("escalation_count", 0)),
    }
