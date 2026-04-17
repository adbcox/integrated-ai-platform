from typing import Any


def run_watchdog(
    compliance: dict[str, Any],
    circuit_result: dict[str, Any],
    health: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(compliance, dict)
        or not isinstance(circuit_result, dict)
        or not isinstance(health, dict)
    ):
        return {
            "watchdog_status": "invalid_input",
            "watchdog_phase": None,
            "alert_reason": None,
        }

    compliant = compliance.get("compliance_status") in ("compliant", "partial")
    circuit_ok = circuit_result.get("circuit_status") in ("closed", "half_open")
    health_ok = health.get("health_status") in ("healthy", "degraded")
    is_critical = health.get("health_status") == "critical"
    circuit_open = circuit_result.get("circuit_status") == "open"

    if compliant and circuit_ok and health_ok:
        return {
            "watchdog_status": "clear",
            "watchdog_phase": health.get("phase_id"),
            "alert_reason": None,
        }

    if is_critical or circuit_open:
        return {
            "watchdog_status": "critical",
            "watchdog_phase": health.get("phase_id"),
            "alert_reason": "circuit_open" if circuit_open else "health",
        }

    if (not compliant or not circuit_ok) and not is_critical and not circuit_open:
        return {
            "watchdog_status": "alert",
            "watchdog_phase": health.get("phase_id"),
            "alert_reason": "non_compliant" if not compliant else "health",
        }

    return {
        "watchdog_status": "invalid_input",
        "watchdog_phase": None,
        "alert_reason": None,
    }
