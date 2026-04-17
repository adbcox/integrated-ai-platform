from typing import Any


def optimize_trajectory(
    horizon_plan: dict[str, Any],
    strategy: dict[str, Any],
    optimization_config: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(horizon_plan, dict)
        or not isinstance(strategy, dict)
        or not isinstance(optimization_config, dict)
    ):
        return {
            "trajectory_status": "invalid_input",
            "trajectory_phase": None,
            "step_count": 0,
        }

    horizon_ok = horizon_plan.get("horizon_plan_status") == "planned"
    strategy_ok = strategy.get("strategy_status") == "learned"

    if horizon_ok and strategy_ok:
        return {
            "trajectory_status": "optimized",
            "trajectory_phase": horizon_plan.get("horizon_phase"),
            "step_count": horizon_plan.get("horizon_depth", 0),
        }

    if not horizon_ok:
        return {
            "trajectory_status": "no_plan",
            "trajectory_phase": None,
            "step_count": 0,
        }

    return {
        "trajectory_status": "invalid_input",
        "trajectory_phase": None,
        "step_count": 0,
    }
