from typing import Any


def schedule_priority_jobs(
    batch_plan: dict[str, Any],
    priority_map: dict[str, Any],
) -> dict[str, Any]:
    if not isinstance(batch_plan, dict) or not isinstance(priority_map, dict):
        return {
            "schedule_status": "invalid_input",
            "scheduled_count": 0,
            "priority_levels": [],
        }

    plan_status = batch_plan.get("plan_status")

    if plan_status != "planned":
        return {
            "schedule_status": "batch_not_planned",
            "scheduled_count": 0,
            "priority_levels": [],
        }

    if len(priority_map) == 0:
        return {
            "schedule_status": "no_priorities",
            "scheduled_count": 0,
            "priority_levels": [],
        }

    return {
        "schedule_status": "scheduled",
        "scheduled_count": batch_plan.get("batch_size", 0),
        "priority_levels": sorted(list(priority_map.keys())),
    }
