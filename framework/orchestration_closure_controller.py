from typing import Any


def control_closure_state(
    closure_steps: list[str], completed_steps: list[str], failed_steps: list[str]
) -> dict[str, Any]:
    if (
        not isinstance(closure_steps, list)
        or not isinstance(completed_steps, list)
        or not isinstance(failed_steps, list)
    ):
        return {
            "controller_valid": False,
            "total_steps": 0,
            "completed_count": 0,
            "failed_count": 0,
            "pending_steps": [],
            "failed_step_list": [],
            "completion_pct": 0.0,
            "controller_status": "invalid_input",
        }

    total_steps = len(closure_steps)
    completed_count = len([s for s in closure_steps if s in completed_steps])
    failed_step_list = [s for s in closure_steps if s in failed_steps]
    failed_count = len(failed_step_list)
    pending_steps = [s for s in closure_steps if s not in completed_steps and s not in failed_steps]
    completion_pct = (
        round((completed_count / float(total_steps)) * 100.0, 3) if total_steps > 0 else 0.0
    )

    if total_steps == 0:
        status = "empty"
    elif completion_pct == 100.0 and failed_count == 0:
        status = "closed"
    elif failed_count > 0 and len(pending_steps) == 0:
        status = "stalled"
    else:
        status = "in_progress"

    return {
        "controller_valid": True,
        "total_steps": total_steps,
        "completed_count": completed_count,
        "failed_count": failed_count,
        "pending_steps": pending_steps,
        "failed_step_list": failed_step_list,
        "completion_pct": completion_pct,
        "controller_status": status,
    }


def summarize_closure_control(result: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(result, dict) or result.get("controller_valid") is not True:
        return {
            "summary_valid": False,
            "controller_status": "invalid_input",
            "completion_pct": 0.0,
            "pending_step_count": 0,
        }

    return {
        "summary_valid": True,
        "controller_status": result.get("controller_status", "invalid_input"),
        "completion_pct": float(result.get("completion_pct", 0.0)),
        "pending_step_count": (
            len(result.get("pending_steps", []))
            if isinstance(result.get("pending_steps", []), list)
            else 0
        ),
    }
