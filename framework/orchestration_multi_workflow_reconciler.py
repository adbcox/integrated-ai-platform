from typing import Any


def reconcile_multi_workflow(session_summaries: list[dict[str, Any]]) -> dict[str, Any]:
    if not isinstance(session_summaries, list):
        return {
            "reconcile_valid": False,
            "workflow_count": 0,
            "success_count": 0,
            "partial_count": 0,
            "failed_count": 0,
            "unarchived_count": 0,
            "total_completed_jobs": 0,
            "total_failed_jobs": 0,
            "mean_elapsed": 0.0,
            "divergence_detected": False,
            "reconcile_status": "invalid_input",
        }

    valid = [
        s
        for s in session_summaries
        if isinstance(s, dict) and s.get("summary_valid") is True
    ]

    if len(valid) == 0:
        return {
            "reconcile_valid": True,
            "workflow_count": 0,
            "success_count": 0,
            "partial_count": 0,
            "failed_count": 0,
            "unarchived_count": 0,
            "total_completed_jobs": 0,
            "total_failed_jobs": 0,
            "mean_elapsed": 0.0,
            "divergence_detected": False,
            "reconcile_status": "empty",
        }

    success_count = len([s for s in valid if s.get("session_outcome") == "success"])
    partial_count = len([s for s in valid if s.get("session_outcome") == "partial"])
    failed_count = len([s for s in valid if s.get("session_outcome") == "failed"])
    unarchived_count = len(
        [s for s in valid if s.get("session_outcome") == "unarchived"]
    )
    total_completed_jobs = sum(int(s.get("completed_count", 0)) for s in valid)
    total_failed_jobs = sum(int(s.get("failed_count", 0)) for s in valid)
    mean_elapsed = round(
        sum(float(s.get("elapsed_seconds", 0.0)) for s in valid) / float(len(valid)),
        3,
    )
    divergence_detected = success_count > 0 and failed_count > 0

    return {
        "reconcile_valid": True,
        "workflow_count": len(valid),
        "success_count": success_count,
        "partial_count": partial_count,
        "failed_count": failed_count,
        "unarchived_count": unarchived_count,
        "total_completed_jobs": total_completed_jobs,
        "total_failed_jobs": total_failed_jobs,
        "mean_elapsed": mean_elapsed,
        "divergence_detected": divergence_detected,
        "reconcile_status": "divergent" if divergence_detected else "consistent",
    }


def summarize_multi_workflow_reconciliation(
    result: dict[str, Any],
) -> dict[str, Any]:
    if not isinstance(result, dict) or result.get("reconcile_valid") is not True:
        return {
            "summary_valid": False,
            "reconcile_status": "invalid_input",
            "workflow_count": 0,
            "divergence_detected": False,
        }

    return {
        "summary_valid": True,
        "reconcile_status": result.get("reconcile_status", "invalid_input"),
        "workflow_count": int(result.get("workflow_count", 0)),
        "divergence_detected": bool(result.get("divergence_detected", False)),
    }
