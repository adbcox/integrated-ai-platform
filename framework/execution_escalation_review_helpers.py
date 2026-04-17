from typing import Any

def generate_escalation_review(
    all_jobs: list[dict[str, Any]],
    job_events: list[dict[str, Any]],
) -> dict[str, Any]:
    escalations = []
    escalation_patterns = {}
    for event in job_events:
        if not isinstance(event, dict):
            continue
        if event.get("event_type") != "escalated":
            continue
        job_id = event.get("job_id", "unknown")
        reason = event.get("detail", "unspecified")
        pattern_key = reason.lower().strip()
        if pattern_key not in escalation_patterns:
            escalation_patterns[pattern_key] = 0
        escalation_patterns[pattern_key] += 1
        escalations.append({
            "job_id": job_id,
            "reason": reason,
            "timestamp": event.get("timestamp", "unknown"),
        })
    return {
        "escalation_count": len(escalations),
        "pattern_distribution": escalation_patterns,
        "escalations": escalations,
    }
