from typing import Any


def control_escalation(
    watchdog: dict[str, Any],
    recovery_cp: dict[str, Any],
    escalation_policy: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(watchdog, dict)
        or not isinstance(recovery_cp, dict)
        or not isinstance(escalation_policy, dict)
    ):
        return {
            "escalation_status": "invalid_input",
            "escalation_level": None,
            "escalation_phase": None,
        }

    needs_escalation = watchdog.get("watchdog_status") in ("alert", "critical")
    cp_ready = recovery_cp.get("recovery_cp_status") == "operational"

    if watchdog.get("watchdog_status") == "clear":
        return {
            "escalation_status": "monitoring",
            "escalation_level": None,
            "escalation_phase": None,
        }

    if needs_escalation and cp_ready:
        return {
            "escalation_status": "escalated",
            "escalation_level": watchdog.get("watchdog_status"),
            "escalation_phase": recovery_cp.get("recovery_phase"),
        }

    if needs_escalation and not cp_ready:
        return {
            "escalation_status": "blocked",
            "escalation_level": None,
            "escalation_phase": None,
        }

    return {
        "escalation_status": "invalid_input",
        "escalation_level": None,
        "escalation_phase": None,
    }
