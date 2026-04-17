from typing import Any

def compute_retry_burden_summary(
    job_events: list[dict[str, Any]],
) -> dict[str, Any]:
    jobs_with_retries = {}
    total_retries = 0
    escalated_after_retry = 0
    for event in job_events:
        if not isinstance(event, dict):
            continue
        job_id = event.get("job_id", "unknown")
        if event.get("event_type") == "retry_triggered":
            total_retries += 1
            if job_id not in jobs_with_retries:
                jobs_with_retries[job_id] = {
                    "retry_count": 0,
                    "reasons": [],
                    "escalated": False,
                }
            jobs_with_retries[job_id]["retry_count"] += 1
            reason = event.get("detail", "unknown_reason")
            if reason not in jobs_with_retries[job_id]["reasons"]:
                jobs_with_retries[job_id]["reasons"].append(reason)
        if event.get("event_type") == "escalated" and job_id in jobs_with_retries:
            jobs_with_retries[job_id]["escalated"] = True
            escalated_after_retry += 1
    return {
        "total_retry_events": total_retries,
        "jobs_affected": len(jobs_with_retries),
        "escalated_after_retry": escalated_after_retry,
        "job_details": jobs_with_retries,
    }
