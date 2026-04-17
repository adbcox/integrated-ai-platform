from typing import Any


def monitor_sla(
    health: dict[str, Any],
    resilience_cp: dict[str, Any],
    sla_config: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(health, dict)
        or not isinstance(resilience_cp, dict)
        or not isinstance(sla_config, dict)
    ):
        return {
            "sla_status": "invalid_input",
            "sla_phase": None,
            "risk_factor": None,
        }

    health_status = health.get("health_status")
    cp_status = resilience_cp.get("resilience_cp_status")

    if health_status == "healthy" and cp_status == "operational":
        return {
            "sla_status": "met",
            "sla_phase": health.get("phase_id"),
            "risk_factor": None,
        }

    if (
        (health_status == "degraded" or cp_status == "degraded")
        and health_status != "critical"
        and cp_status != "offline"
    ):
        return {
            "sla_status": "at_risk",
            "sla_phase": health.get("phase_id"),
            "risk_factor": health_status,
        }

    if health_status == "critical" or cp_status == "offline":
        return {
            "sla_status": "breached",
            "sla_phase": health.get("phase_id"),
            "risk_factor": health_status,
        }

    return {
        "sla_status": "invalid_input",
        "sla_phase": None,
        "risk_factor": None,
    }
