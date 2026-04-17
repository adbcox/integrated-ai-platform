from typing import Any


def execute_replay_step(
    replay_plan: dict[str, Any], replay_state: dict[str, Any]
) -> dict[str, Any]:
    if not isinstance(replay_plan, dict) or not isinstance(replay_state, dict):
        return {
            "execution_valid": False,
            "current_step_index": -1,
            "current_job_id": "",
            "steps_completed": 0,
            "steps_remaining": 0,
            "replay_execution_status": "invalid_input",
        }

    if replay_plan.get("replay_plan_status") not in ("planned", "empty"):
        return {
            "execution_valid": False,
            "current_step_index": -1,
            "current_job_id": "",
            "steps_completed": 0,
            "steps_remaining": 0,
            "replay_execution_status": "invalid_input",
        }

    execution_steps = replay_plan.get("execution_steps", [])
    step_count = int(replay_plan.get("step_count", 0))
    if not isinstance(execution_steps, list):
        execution_steps = []

    if step_count == 0 or len(execution_steps) == 0:
        return {
            "execution_valid": True,
            "current_step_index": -1,
            "current_job_id": "",
            "steps_completed": 0,
            "steps_remaining": 0,
            "replay_execution_status": "no_steps",
        }

    completed = (
        set(replay_state.get("completed_step_indices", []))
        if isinstance(replay_state.get("completed_step_indices", []), list)
        else set()
    )
    failed = (
        set(replay_state.get("failed_step_indices", []))
        if isinstance(replay_state.get("failed_step_indices", []), list)
        else set()
    )

    current = None
    for step in sorted(
        [s for s in execution_steps if isinstance(s, dict)],
        key=lambda s: int(s.get("step_index", 0)),
    ):
        idx = int(step.get("step_index", -1))
        if idx not in completed and idx not in failed:
            current = step
            break

    if current is None:
        return {
            "execution_valid": True,
            "current_step_index": -1,
            "current_job_id": "",
            "steps_completed": len(completed),
            "steps_remaining": max(0, step_count - len(completed) - len(failed)),
            "replay_execution_status": "complete",
        }

    return {
        "execution_valid": True,
        "current_step_index": int(current.get("step_index", -1)),
        "current_job_id": current.get("job_id", ""),
        "steps_completed": len(completed),
        "steps_remaining": max(0, step_count - len(completed) - len(failed)),
        "replay_execution_status": "advanced",
    }


def summarize_replay_execution(result: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(result, dict) or result.get("execution_valid") is not True:
        return {
            "summary_valid": False,
            "replay_execution_status": "invalid_input",
            "steps_completed": 0,
            "steps_remaining": 0,
        }

    return {
        "summary_valid": True,
        "replay_execution_status": result.get("replay_execution_status", "invalid_input"),
        "steps_completed": int(result.get("steps_completed", 0)),
        "steps_remaining": int(result.get("steps_remaining", 0)),
    }
