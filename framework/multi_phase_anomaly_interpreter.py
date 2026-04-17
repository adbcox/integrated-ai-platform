from typing import Any


def interpret_anomaly(
    metrics: dict[str, Any],
    health: dict[str, Any],
    threshold: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(metrics, dict)
        or not isinstance(health, dict)
        or not isinstance(threshold, dict)
    ):
        return {
            "anomaly_status": "invalid_input",
            "anomaly_phase": None,
            "anomaly_type": None,
        }

    metrics_ok = metrics.get("metrics_status") == "collected"
    is_anomalous = health.get("health_status") in ("degraded", "critical")

    if metrics_ok and is_anomalous:
        return {
            "anomaly_status": "detected",
            "anomaly_phase": metrics.get("collected_phase"),
            "anomaly_type": health.get("health_status"),
        }

    if metrics_ok and not is_anomalous:
        return {
            "anomaly_status": "none",
            "anomaly_phase": None,
            "anomaly_type": None,
        }

    return {
        "anomaly_status": "invalid_input",
        "anomaly_phase": None,
        "anomaly_type": None,
    }
