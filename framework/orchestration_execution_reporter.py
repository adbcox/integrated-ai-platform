from typing import Any


def generate_execution_report(
    plan: dict[str, Any],
    completed_job_ids: list[str],
    failed_job_ids: list[str],
    elapsed_seconds: float,
) -> dict[str, Any]:
    if (
        not isinstance(plan, dict)
        or not isinstance(completed_job_ids, list)
        or not isinstance(failed_job_ids, list)
    ):
        return {
            "report_valid": False,
            "plan_id": "unknown",
            "total_jobs": 0,
            "completed_count": 0,
            "failed_count": 0,
            "elapsed_seconds": 0.0,
            "throughput_jobs_per_sec": 0.0,
            "report_status": "invalid_input",
        }

    total_jobs = int(plan.get("total_jobs", 0))
    completed_count = len(completed_job_ids)
    failed_count = len(failed_job_ids)

    throughput = (
        round((completed_count / float(elapsed_seconds)), 3)
        if elapsed_seconds > 0
        else 0.0
    )

    report_status = "invalid_input"
    if failed_count == 0 and completed_count == total_jobs:
        report_status = "complete"
    elif failed_count > 0 and completed_count > 0:
        report_status = "partial"
    elif failed_count > 0 and completed_count == 0:
        report_status = "failed"
    elif failed_count == 0 and completed_count < total_jobs:
        report_status = "partial"

    return {
        "report_valid": True,
        "plan_id": plan.get("plan_id", "unknown"),
        "total_jobs": total_jobs,
        "completed_count": completed_count,
        "failed_count": failed_count,
        "elapsed_seconds": float(elapsed_seconds),
        "throughput_jobs_per_sec": throughput,
        "report_status": report_status,
    }


def summarize_execution_report(result: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(result, dict) or result.get("report_valid") is not True:
        return {
            "summary_valid": False,
            "report_status": "invalid_input",
            "completed_count": 0,
            "failed_count": 0,
        }

    return {
        "summary_valid": True,
        "report_status": result.get("report_status", "invalid_input"),
        "completed_count": int(result.get("completed_count", 0)),
        "failed_count": int(result.get("failed_count", 0)),
    }
