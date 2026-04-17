from typing import Any


def plan_resumption_execution(
    resumption_result: dict[str, Any],
    retry_policy: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(resumption_result, dict)
        or not isinstance(retry_policy, dict)
    ):
        return {
            "plan_valid": False,
            "execution_steps": [],
            "step_count": 0,
            "has_retries": False,
            "resumption_plan_status": "invalid_input",
        }

    if resumption_result.get("resumption_action") == "invalid_input":
        return {
            "plan_valid": False,
            "execution_steps": [],
            "step_count": 0,
            "has_retries": False,
            "resumption_plan_status": "invalid_input",
        }

    if resumption_result.get("resumption_action") == "complete":
        return {
            "plan_valid": True,
            "execution_steps": [],
            "step_count": 0,
            "has_retries": False,
            "resumption_plan_status": "empty",
        }

    execution_steps = []
    base_delay = float(retry_policy.get("base_delay_seconds", 0.0))
    retry_candidates = resumption_result.get("retry_candidates", [])
    jobs_pending = resumption_result.get("jobs_pending", [])

    if not isinstance(retry_candidates, list):
        retry_candidates = []
    if not isinstance(jobs_pending, list):
        jobs_pending = []

    step_index = 0

    for job_id in retry_candidates:
        execution_steps.append(
            {
                "step_index": step_index,
                "job_id": job_id,
                "step_type": "retry",
                "delay_seconds": base_delay,
            }
        )
        step_index += 1

    for job_id in jobs_pending:
        execution_steps.append(
            {
                "step_index": step_index,
                "job_id": job_id,
                "step_type": "resume",
                "delay_seconds": 0.0,
            }
        )
        step_index += 1

    status = "planned" if execution_steps else "empty"

    return {
        "plan_valid": True,
        "execution_steps": execution_steps,
        "step_count": len(execution_steps),
        "has_retries": any(
            step.get("step_type") == "retry" for step in execution_steps
        ),
        "resumption_plan_status": status,
    }


def summarize_resumption_plan(result: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(result, dict) or result.get("plan_valid") is not True:
        return {
            "summary_valid": False,
            "step_count": 0,
            "has_retries": False,
            "resumption_plan_status": "invalid_input",
        }

    return {
        "summary_valid": True,
        "step_count": int(result.get("step_count", 0)),
        "has_retries": bool(result.get("has_retries", False)),
        "resumption_plan_status": result.get(
            "resumption_plan_status", "invalid_input"
        ),
    }
