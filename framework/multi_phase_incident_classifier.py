from typing import Any


def classify_incident(
    anomaly: dict[str, Any],
    watchdog: dict[str, Any],
    sla: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(anomaly, dict)
        or not isinstance(watchdog, dict)
        or not isinstance(sla, dict)
    ):
        return {
            "incident_status": "invalid_input",
            "incident_phase": None,
            "severity": "invalid_input",
        }

    anomaly_detected = anomaly.get("anomaly_status") == "detected"
    watchdog_critical = watchdog.get("watchdog_status") == "critical"
    sla_breached = sla.get("sla_status") == "breached"

    if anomaly_detected and (watchdog_critical or sla_breached):
        return {
            "incident_status": "critical",
            "incident_phase": anomaly.get("anomaly_phase"),
            "severity": "critical",
        }

    if anomaly_detected and not watchdog_critical and not sla_breached:
        return {
            "incident_status": "warning",
            "incident_phase": anomaly.get("anomaly_phase"),
            "severity": "warning",
        }

    if not anomaly_detected:
        return {
            "incident_status": "nominal",
            "incident_phase": None,
            "severity": "nominal",
        }

    return {
        "incident_status": "invalid_input",
        "incident_phase": None,
        "severity": "invalid_input",
    }
