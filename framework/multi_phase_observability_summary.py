from typing import Any


def summarize_observability(
    observability_cp: dict[str, Any],
    sla: dict[str, Any],
    incident: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(observability_cp, dict)
        or not isinstance(sla, dict)
        or not isinstance(incident, dict)
    ):
        return {
            "observability_summary_status": "invalid_input",
            "summary_phase": None,
            "observability_health": "degraded",
        }

    cp_operational = observability_cp.get("observability_cp_status") == "operational"
    sla_ok = sla.get("sla_status") in ("met", "at_risk")
    incident_managed = incident.get("incident_status") in ("critical", "warning", "nominal")

    if cp_operational and sla_ok and incident_managed:
        return {
            "observability_summary_status": "complete",
            "summary_phase": observability_cp.get("observability_phase"),
            "observability_health": "healthy",
        }

    if cp_operational and (not sla_ok or not incident_managed):
        return {
            "observability_summary_status": "partial",
            "summary_phase": None,
            "observability_health": "degraded",
        }

    return {
        "observability_summary_status": "failed",
        "summary_phase": None,
        "observability_health": "degraded",
    }
