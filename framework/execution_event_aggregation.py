from typing import Any

def aggregate_events_by_job(events: list[dict[str, Any]]) -> dict[str, Any]:
    if not events:
        return {}
    job_events = {}
    for event in events:
        if not isinstance(event, dict):
            continue
        job_id = event.get("job_id")
        if not job_id:
            continue
        if job_id not in job_events:
            job_events[job_id] = []
        job_events[job_id].append(event)
    return {job_id: job_events[job_id] for job_id in sorted(job_events.keys())}

def compute_event_statistics(events: list[dict[str, Any]]) -> dict[str, Any]:
    if not events:
        return {"total_events": 0, "unique_jobs": 0, "event_type_counts": {}, "event_types_present": []}
    type_counts = {}
    job_ids = set()
    valid_events = 0
    for event in events:
        if not isinstance(event, dict):
            continue
        valid_events += 1
        event_type = event.get("event_type")
        if event_type:
            type_counts[event_type] = type_counts.get(event_type, 0) + 1
        job_id = event.get("job_id")
        if job_id:
            job_ids.add(job_id)
    return {
        "total_events": valid_events,
        "unique_jobs": len(job_ids),
        "event_type_counts": {k: type_counts[k] for k in sorted(type_counts.keys())},
        "event_types_present": sorted(list(type_counts.keys()))
    }

def compute_job_execution_duration(job_events: list[dict[str, Any]]) -> dict[str, Any]:
    if not job_events or len(job_events) < 2:
        return {"duration_seconds": 0, "start_time": None, "end_time": None}
    timestamps = [e.get("timestamp_utc") for e in job_events if isinstance(e, dict) and e.get("timestamp_utc")]
    if len(timestamps) < 2:
        return {"duration_seconds": 0, "start_time": None, "end_time": None}
    timestamps_sorted = sorted(timestamps)
    return {
        "start_time": timestamps_sorted[0],
        "end_time": timestamps_sorted[-1],
        "duration_seconds": len(timestamps_sorted) - 1
    }

def get_event_timeline_summary(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not events:
        return []
    sorted_events = sorted(
        [e for e in events if isinstance(e, dict)],
        key=lambda x: x.get("timestamp_utc", "")
    )
    summary = []
    for event in sorted_events[:20]:
        summary.append({
            "timestamp": event.get("timestamp_utc"),
            "job_id": event.get("job_id"),
            "event_type": event.get("event_type"),
            "state": event.get("lifecycle_state")
        })
    return summary
