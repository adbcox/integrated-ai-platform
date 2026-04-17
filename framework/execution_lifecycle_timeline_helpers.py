from typing import Any

def render_lifecycle_timeline(
    job_id: str,
    lifecycle_events: list[dict[str, Any]],
) -> dict[str, Any]:
    if not lifecycle_events:
        return {
            "job_id": job_id,
            "timeline": [],
            "event_count": 0,
        }
    timeline = []
    for event in lifecycle_events:
        if not isinstance(event, dict):
            continue
        timeline.append({
            "timestamp": event.get("timestamp", "unknown"),
            "state": event.get("state", "unknown"),
            "reason": event.get("reason", ""),
        })
    return {
        "job_id": job_id,
        "timeline": timeline,
        "event_count": len(timeline),
    }
