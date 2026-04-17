from typing import Any

def bridge_plan_to_execution(
    plan_target: str,
    runtime_context: dict[str, Any],
) -> dict[str, Any]:
    if not plan_target or not isinstance(plan_target, str):
        return {
            "execution_target": "unknown",
            "mapping_valid": False,
            "error": "invalid_plan_target",
        }
    execution_target = plan_target.replace("plan::", "exec::")
    return {
        "plan_target": plan_target,
        "execution_target": execution_target,
        "mapping_valid": True,
        "runtime_context_applied": isinstance(runtime_context, dict),
    }
