from typing import Any

def validate_event_consistency(
    events: list[dict[str, Any]],
) -> dict[str, Any]:
    if not events:
        return {
            "validation_valid": True,
            "errors": [],
        }
    errors = []
    retry_counts = {}
    known_job_ids = set()
    for event in events:
        if not isinstance(event, dict):
            continue
        job_id = event.get("job_id", "unknown")
        known_job_ids.add(job_id)
        if event.get("event_type") == "retry_triggered":
            retry_counts[job_id] = retry_counts.get(job_id, 0) + 1
    for event in events:
        if not isinstance(event, dict):
            continue
        job_id = event.get("job_id", "unknown")
        if event.get("event_type") == "escalated" and job_id not in known_job_ids:
            errors.append("Escalation event for unknown job {}".format(job_id))
    return {
        "validation_valid": len(errors) == 0,
        "errors": errors,
    }
