from typing import Any


def balance_phase_load(
    phase_demand: int,
    available_capacity: int,
    active_phases: int,
) -> dict[str, Any]:
    if (
        not isinstance(phase_demand, int)
        or not isinstance(available_capacity, int)
        or not isinstance(active_phases, int)
    ):
        return {
            "load_status": "invalid_input",
            "load_factor": None,
            "overloaded": False,
        }

    if available_capacity <= 0:
        return {
            "load_status": "invalid_input",
            "load_factor": None,
            "overloaded": False,
        }

    if active_phases <= 0:
        return {
            "load_status": "invalid_input",
            "load_factor": None,
            "overloaded": False,
        }

    load_factor = phase_demand / available_capacity if available_capacity > 0 else 0
    per_phase_capacity = available_capacity / active_phases

    if phase_demand > per_phase_capacity:
        return {
            "load_status": "overloaded",
            "load_factor": load_factor,
            "overloaded": True,
        }

    if load_factor >= 0.8:
        return {
            "load_status": "high_load",
            "load_factor": load_factor,
            "overloaded": False,
        }

    return {
        "load_status": "balanced",
        "load_factor": load_factor,
        "overloaded": False,
    }
