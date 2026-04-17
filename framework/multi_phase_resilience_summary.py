from typing import Any


def summarize_resilience_subsystem(
    resilience_cp: dict[str, Any],
    budget_manager: dict[str, Any],
    circuit_breaker: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(resilience_cp, dict)
        or not isinstance(budget_manager, dict)
        or not isinstance(circuit_breaker, dict)
    ):
        return {
            "summary_status": "invalid_input",
            "subsystem_health": None,
            "subsystem_operational": False,
        }

    cp_ok = resilience_cp.get("resilience_cp_status") == "operational"
    budget_ok = budget_manager.get("budget_status") in ("available", "last_attempt")
    circuit_ok = circuit_breaker.get("circuit_state") in ("closed", "half_open")

    all_ok = cp_ok and budget_ok and circuit_ok

    if not cp_ok:
        return {
            "summary_status": "control_plane_not_operational",
            "subsystem_health": None,
            "subsystem_operational": False,
        }

    if circuit_breaker.get("circuit_state") == "open":
        return {
            "summary_status": "circuit_open",
            "subsystem_health": "degraded",
            "subsystem_operational": False,
        }

    if budget_manager.get("budget_depleted") is True:
        return {
            "summary_status": "budget_depleted",
            "subsystem_health": "degraded",
            "subsystem_operational": False,
        }

    if all_ok:
        return {
            "summary_status": "healthy",
            "subsystem_health": "healthy",
            "subsystem_operational": True,
        }

    return {
        "summary_status": "partially_operational",
        "subsystem_health": "degraded",
        "subsystem_operational": False,
    }
