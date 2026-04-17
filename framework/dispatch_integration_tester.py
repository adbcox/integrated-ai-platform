from typing import Any

from framework.dispatch_execution_router import route_dispatch_execution
from framework.dispatch_fallback_scheduler import schedule_dispatch_fallback


def run_dispatch_integration_test(
    job: dict[str, Any],
    health_score: int,
    coherence_valid: bool,
    next_eligible_seconds: int,
    target_pool: list[str],
) -> dict[str, Any]:
    if not isinstance(job, dict) or not isinstance(target_pool, list):
        return {
            "test_valid": False,
            "dispatch_attempted": False,
            "fallback_scheduled": False,
            "failure_reason": "invalid_input",
        }

    route = route_dispatch_execution(
        job,
        health_score,
        coherence_valid,
        next_eligible_seconds,
        target_pool,
    )

    if not route.get("route_valid", False):
        fallback = schedule_dispatch_fallback(
            job.get("job_id", ""),
            1,
            route.get("route_reason", "route_failed"),
            "2026-04-17T00:00:00Z",
            3,
        )
        return {
            "test_valid": True,
            "dispatch_attempted": False,
            "fallback_scheduled": fallback.get("schedule_valid", False),
            "failure_reason": route.get("route_reason", "route_failed"),
        }

    return {
        "test_valid": True,
        "dispatch_attempted": True,
        "fallback_scheduled": False,
        "failure_reason": "",
    }


def summarize_integration_results(
    results: list[dict[str, Any]],
) -> dict[str, Any]:
    if not isinstance(results, list):
        return {
            "summary_valid": False,
            "test_count": 0,
            "passed_count": 0,
            "failed_count": 0,
        }

    valid = [r for r in results if isinstance(r, dict)]
    passed = len([r for r in valid if r.get("failure_reason", "") == ""])
    failed = len(valid) - passed

    return {
        "summary_valid": True,
        "test_count": len(valid),
        "passed_count": passed,
        "failed_count": failed,
    }
