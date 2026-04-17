from typing import Any

def check_dispatch_readiness(
    job: dict[str, Any],
    health_score: int,
    coherence_valid: bool,
) -> dict[str, Any]:
    if not isinstance(job, dict):
        return {
            "readiness_valid": False,
            "readiness_score": 0,
            "blocking_factors": ["invalid_job_object"],
        }
    blocking_factors = []
    readiness_score = 100
    if health_score < 50:
        blocking_factors.append("poor_health_score")
        readiness_score -= 30
    if not coherence_valid:
        blocking_factors.append("coherence_invalid")
        readiness_score -= 40
    job_status = job.get("lifecycle", "unknown")
    if job_status not in ["accepted", "queued"]:
        blocking_factors.append("invalid_job_status_{}".format(job_status))
        readiness_score -= 50
    readiness_score = max(0, readiness_score)
    return {
        "readiness_valid": len(blocking_factors) == 0,
        "readiness_score": readiness_score,
        "blocking_factors": blocking_factors,
    }
