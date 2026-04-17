from typing import Any


def plan_phase_batch(
    coordinator: dict[str, Any],
    jobs: list[Any],
    health: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(coordinator, dict)
        or not isinstance(jobs, list)
        or not isinstance(health, dict)
    ):
        return {
            "plan_status": "invalid_input",
            "batch_size": 0,
            "phase_id": None,
        }

    coordinator_status = coordinator.get("coordinator_status")
    health_status = health.get("health_status")

    plan_allowed = (
        coordinator_status == "initialized"
        and health_status in ("healthy", "degraded")
    )

    if health_status == "critical":
        return {
            "plan_status": "health_critical",
            "batch_size": 0,
            "phase_id": coordinator.get("phase_id"),
        }

    if not plan_allowed:
        return {
            "plan_status": "invalid_input",
            "batch_size": 0,
            "phase_id": coordinator.get("phase_id"),
        }

    if len(jobs) == 0:
        return {
            "plan_status": "empty_batch",
            "batch_size": 0,
            "phase_id": coordinator.get("phase_id"),
        }

    return {
        "plan_status": "planned",
        "batch_size": len(jobs),
        "phase_id": coordinator.get("phase_id"),
    }
