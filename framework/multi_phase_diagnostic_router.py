from typing import Any


def route_diagnostic(
    incident: dict[str, Any],
    coordinator: dict[str, Any],
    routing_map: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(incident, dict)
        or not isinstance(coordinator, dict)
        or not isinstance(routing_map, dict)
    ):
        return {
            "diagnostic_status": "invalid_input",
            "routed_to": None,
            "incident_severity": None,
        }

    has_incident = incident.get("incident_status") in ("critical", "warning")
    coord_ok = coordinator.get("coordinator_status") == "initialized"

    if incident.get("incident_status") == "nominal":
        return {
            "diagnostic_status": "no_incident",
            "routed_to": None,
            "incident_severity": None,
        }

    if has_incident and not coord_ok:
        return {
            "diagnostic_status": "coordinator_not_ready",
            "routed_to": None,
            "incident_severity": None,
        }

    if has_incident and coord_ok and len(routing_map) > 0:
        return {
            "diagnostic_status": "routed",
            "routed_to": list(routing_map.keys())[0],
            "incident_severity": incident.get("incident_status"),
        }

    return {
        "diagnostic_status": "invalid_input",
        "routed_to": None,
        "incident_severity": None,
    }
