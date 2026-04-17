from typing import Any


def correlate_alerts(
    anomaly: dict[str, Any],
    incident: dict[str, Any],
    watchdog: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(anomaly, dict)
        or not isinstance(incident, dict)
        or not isinstance(watchdog, dict)
    ):
        return {
            "correlation_status": "invalid_input",
            "signal_count": 0,
            "highest_severity": "none",
        }

    has_anomaly = anomaly.get("anomaly_status") == "detected"
    has_incident = incident.get("incident_status") in ("critical", "warning")
    has_alert = watchdog.get("watchdog_status") in ("alert", "critical")

    any_signal = has_anomaly or has_incident or has_alert
    signal_count = sum([has_anomaly, has_incident, has_alert])

    if any_signal:
        highest = (
            "critical"
            if incident.get("incident_status") == "critical"
            or watchdog.get("watchdog_status") == "critical"
            else "warning"
        )
        return {
            "correlation_status": "correlated",
            "signal_count": signal_count,
            "highest_severity": highest,
        }

    return {
        "correlation_status": "no_alerts",
        "signal_count": 0,
        "highest_severity": "none",
    }
