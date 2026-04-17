from typing import Any


def summarize_orchestration_readiness(
    plan: dict[str, Any],
    dependency_result: dict[str, Any],
    batch_result: dict[str, Any],
    context_result: dict[str, Any],
    advance_result: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(plan, dict)
        or not isinstance(dependency_result, dict)
        or not isinstance(batch_result, dict)
        or not isinstance(context_result, dict)
        or not isinstance(advance_result, dict)
    ):
        return {
            "readiness_valid": False,
            "plan_ready": False,
            "dependencies_ready": False,
            "batches_ready": False,
            "context_ready": False,
            "execution_ready": False,
            "overall_ready": False,
            "blocking_flags": [],
            "readiness_status": "invalid_input",
        }

    plan_ready = plan.get("plan_valid") is True
    dependencies_ready = dependency_result.get("resolution_valid") is True
    batches_ready = batch_result.get("batch_valid") is True
    context_ready = context_result.get("context_valid") is True
    execution_ready = (
        advance_result.get("advance_valid") is True
        and advance_result.get("advance_status")
        not in ("blocked", "invalid_input")
    )

    flags = [
        ("plan_ready", plan_ready),
        ("dependencies_ready", dependencies_ready),
        ("batches_ready", batches_ready),
        ("context_ready", context_ready),
        ("execution_ready", execution_ready),
    ]

    blocking_flags = sorted([name for name, value in flags if not value])
    overall_ready = len(blocking_flags) == 0
    readiness_status = "ready" if overall_ready else "blocked"

    return {
        "readiness_valid": True,
        "plan_ready": plan_ready,
        "dependencies_ready": dependencies_ready,
        "batches_ready": batches_ready,
        "context_ready": context_ready,
        "execution_ready": execution_ready,
        "overall_ready": overall_ready,
        "blocking_flags": blocking_flags,
        "readiness_status": readiness_status,
    }


def summarize_readiness(result: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(result, dict) or result.get("readiness_valid") is not True:
        return {
            "summary_valid": False,
            "overall_ready": False,
            "blocking_flag_count": 0,
            "readiness_status": "invalid_input",
        }

    return {
        "summary_valid": True,
        "overall_ready": bool(result.get("overall_ready", False)),
        "blocking_flag_count": (
            len(result.get("blocking_flags", []))
            if isinstance(result.get("blocking_flags", []), list)
            else 0
        ),
        "readiness_status": result.get("readiness_status", "invalid_input"),
    }
