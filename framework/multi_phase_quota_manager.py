from typing import Any


def manage_phase_quota(
    capacity_plan: dict[str, Any],
    phase_id: str,
    quota_percentage: float,
) -> dict[str, Any]:
    if (
        not isinstance(capacity_plan, dict)
        or not isinstance(phase_id, str)
        or not isinstance(quota_percentage, (int, float))
    ):
        return {
            "quota_status": "invalid_input",
            "allocated_quota": 0,
            "quota_enforced": False,
        }

    if not phase_id or quota_percentage <= 0 or quota_percentage > 100:
        return {
            "quota_status": "invalid_input",
            "allocated_quota": 0,
            "quota_enforced": False,
        }

    plan_status = capacity_plan.get("plan_status")
    if plan_status not in ("sufficient", "minor_expansion", "major_expansion"):
        return {
            "quota_status": "no_plan",
            "allocated_quota": 0,
            "quota_enforced": False,
        }

    required_capacity = capacity_plan.get("required_capacity", 0)
    if required_capacity <= 0:
        return {
            "quota_status": "no_capacity",
            "allocated_quota": 0,
            "quota_enforced": False,
        }

    allocated = int(required_capacity * (quota_percentage / 100))

    return {
        "quota_status": "allocated",
        "allocated_quota": allocated,
        "quota_enforced": True,
    }
