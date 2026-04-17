from typing import Any


def simulate_scenarios(
    scenarios: dict[str, Any],
    coordinator: dict[str, Any],
    config: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(scenarios, dict)
        or not isinstance(coordinator, dict)
        or not isinstance(config, dict)
    ):
        return {
            "simulation_status": "invalid_input",
            "simulation_phase": None,
            "simulation_count": 0,
        }

    s_ok = scenarios.get("scenario_status") == "generated"
    c_ok = coordinator.get("coordinator_status") == "initialized"
    all_ok = s_ok and c_ok

    if all_ok:
        return {
            "simulation_status": "simulated",
            "simulation_phase": scenarios.get("scenario_phase"),
            "simulation_count": scenarios.get("scenario_count", 0),
        }

    return {
        "simulation_status": "failed",
        "simulation_phase": None,
        "simulation_count": 0,
    }
