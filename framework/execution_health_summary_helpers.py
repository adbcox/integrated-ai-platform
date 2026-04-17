from typing import Any

def compute_execution_health_score(
    jobs: list[dict[str, Any]],
    events: list[dict[str, Any]],
) -> dict[str, Any]:
    if not jobs:
        return {
            "health_score": 100,
            "status": "healthy",
            "job_count": 0,
            "failure_rate": 0.0,
            "escalation_rate": 0.0,
        }
    total_jobs = len(jobs)
    failed_jobs = len([j for j in jobs if isinstance(j, dict) and j.get("lifecycle") == "failed"])
    escalated_jobs = len([j for j in jobs if isinstance(j, dict) and j.get("lifecycle") == "escalated"])
    failure_rate = failed_jobs / total_jobs if total_jobs > 0 else 0.0
    escalation_rate = escalated_jobs / total_jobs if total_jobs > 0 else 0.0
    health_score = max(0, 100 - int(failure_rate * 50) - int(escalation_rate * 30))
    status = "healthy" if health_score >= 80 else "degraded" if health_score >= 50 else "critical"
    return {
        "health_score": health_score,
        "status": status,
        "job_count": total_jobs,
        "failure_rate": round(failure_rate, 3),
        "escalation_rate": round(escalation_rate, 3),
    }
