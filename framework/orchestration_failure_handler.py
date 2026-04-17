from typing import Any


def handle_workflow_failure(
    plan: dict[str, Any],
    failed_job_ids: list[str],
    completed_job_ids: list[str],
    failure_policy: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(plan, dict)
        or not isinstance(failed_job_ids, list)
        or not isinstance(completed_job_ids, list)
        or not isinstance(failure_policy, dict)
    ):
        return {
            "handling_valid": False,
            "action": "abort",
            "affected_job_ids": [],
            "retry_candidates": [],
            "abort_reason": "invalid_input",
        }

    retry_limit = int(failure_policy.get("retry_limit", 0))
    abort_on_any_failure = bool(failure_policy.get("abort_on_any_failure", False))

    if abort_on_any_failure and failed_job_ids:
        return {
            "handling_valid": True,
            "action": "abort",
            "affected_job_ids": list(failed_job_ids),
            "retry_candidates": [],
            "abort_reason": "policy_abort_on_failure",
        }

    if failed_job_ids and retry_limit > 0:
        return {
            "handling_valid": True,
            "action": "retry",
            "affected_job_ids": list(failed_job_ids),
            "retry_candidates": list(failed_job_ids),
            "abort_reason": "",
        }

    if failed_job_ids and retry_limit <= 0:
        return {
            "handling_valid": True,
            "action": "escalate",
            "affected_job_ids": list(failed_job_ids),
            "retry_candidates": [],
            "abort_reason": "",
        }

    return {
        "handling_valid": True,
        "action": "continue",
        "affected_job_ids": [],
        "retry_candidates": [],
        "abort_reason": "",
    }


def summarize_failure_handling(result: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(result, dict):
        return {
            "summary_valid": False,
            "action": "invalid_input",
            "retry_candidates": 0,
        }

    return {
        "summary_valid": bool(result.get("handling_valid", False)),
        "action": result.get("action", "invalid_input"),
        "retry_candidates": (
            len(result.get("retry_candidates", []))
            if isinstance(result.get("retry_candidates", []), list)
            else 0
        ),
    }
