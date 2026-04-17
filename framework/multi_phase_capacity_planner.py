from typing import Any


def plan_capacity(
    total_demand: int,
    current_capacity: int,
    growth_factor: float,
) -> dict[str, Any]:
    if (
        not isinstance(total_demand, int)
        or not isinstance(current_capacity, int)
        or not isinstance(growth_factor, (int, float))
    ):
        return {
            "plan_status": "invalid_input",
            "required_capacity": None,
            "capacity_sufficient": False,
        }

    if current_capacity <= 0 or growth_factor <= 0:
        return {
            "plan_status": "invalid_input",
            "required_capacity": None,
            "capacity_sufficient": False,
        }

    required_capacity = int(total_demand * growth_factor)

    if current_capacity >= required_capacity:
        return {
            "plan_status": "sufficient",
            "required_capacity": required_capacity,
            "capacity_sufficient": True,
        }

    shortfall = required_capacity - current_capacity
    if shortfall <= current_capacity * 0.2:
        return {
            "plan_status": "minor_expansion",
            "required_capacity": required_capacity,
            "capacity_sufficient": False,
        }

    return {
        "plan_status": "major_expansion",
        "required_capacity": required_capacity,
        "capacity_sufficient": False,
    }
