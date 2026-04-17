from typing import Any


def control_preemption(
    incident: dict[str, Any],
    forecast: dict[str, Any],
    preemption_policy: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(incident, dict)
        or not isinstance(forecast, dict)
        or not isinstance(preemption_policy, dict)
    ):
        return {
            "preemption_status": "invalid_input",
            "preempted_phase": None,
            "severity": None,
        }

    incident_active = incident.get("incident_status") in ("critical", "warning")
    forecast_ok = forecast.get("forecast_status") == "forecasted"

    if incident_active and forecast_ok:
        return {
            "preemption_status": "preempted",
            "preempted_phase": incident.get("incident_phase"),
            "severity": incident.get("incident_status"),
        }

    if forecast_ok and incident.get("incident_status") == "nominal":
        return {"preemption_status": "monitoring", "preempted_phase": None, "severity": None}

    if incident.get("incident_status") == "nominal" and not forecast_ok:
        return {
            "preemption_status": "no_incident",
            "preempted_phase": None,
            "severity": None,
        }

    return {
        "preemption_status": "invalid_input",
        "preempted_phase": None,
        "severity": None,
    }
