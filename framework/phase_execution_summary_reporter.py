from typing import Any

def generate_phase_summary_report(
    jobs: list[dict[str, Any]],
    events: list[dict[str, Any]],
) -> dict[str, Any]:
    if not jobs:
        return {
            "report_type": "phase_summary",
            "status": "complete",
            "total_jobs": 0,
            "success_count": 0,
            "failure_count": 0,
            "escalation_count": 0,
            "success_rate": 0.0,
        }
    total_jobs = len(jobs)
    success_count = len([j for j in jobs if isinstance(j, dict) and j.get("lifecycle") == "completed"])
    failure_count = len([j for j in jobs if isinstance(j, dict) and j.get("lifecycle") == "failed"])
    escalation_count = len([j for j in jobs if isinstance(j, dict) and j.get("lifecycle") == "escalated"])
    success_rate = success_count / total_jobs if total_jobs > 0 else 0.0
    return {
        "report_type": "phase_summary",
        "status": "complete",
        "total_jobs": total_jobs,
        "success_count": success_count,
        "failure_count": failure_count,
        "escalation_count": escalation_count,
        "success_rate": round(success_rate, 3),
    }
