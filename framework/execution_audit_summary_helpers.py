from typing import Any

def render_execution_audit_summary(
    job_id: str,
    audit_trail: list[dict[str, Any]],
) -> dict[str, Any]:
    if not audit_trail:
        return {
            "job_id": job_id,
            "narrative": "No audit trail recorded.",
            "decision_points": [],
            "retry_clarity": "none",
        }
    events = []
    retry_count = 0
    for entry in audit_trail:
        if not isinstance(entry, dict):
            continue
        event_type = entry.get("event_type", "unknown")
        if event_type == "retry_triggered":
            retry_count += 1
        events.append({
            "timestamp": entry.get("timestamp", "unknown"),
            "event_type": event_type,
            "detail": entry.get("detail", ""),
        })
    narrative = "Job {}: {} events, {} retries.".format(job_id, len(events), retry_count)
    return {
        "job_id": job_id,
        "narrative": narrative,
        "decision_points": events,
        "retry_clarity": "retried" if retry_count > 0 else "none",
    }
