from typing import Any


def build_operational_dashboard(
    health_result: dict[str, Any],
    throughput_result: dict[str, Any],
    anomaly_result: dict[str, Any],
    alert_result: dict[str, Any],
    integration_result: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(health_result, dict)
        or not isinstance(throughput_result, dict)
        or not isinstance(anomaly_result, dict)
        or not isinstance(alert_result, dict)
        or not isinstance(integration_result, dict)
    ):
        return {
            "dashboard_valid": False,
            "health_status": "unknown",
            "health_score": 0.0,
            "mean_throughput": 0.0,
            "anomaly_status": "unknown",
            "alert_count": 0,
            "critical_count": 0,
            "integration_status": "unknown",
            "overall_operational_status": "invalid_input",
            "dashboard_status": "invalid_input",
        }

    health_status = health_result.get("health_status", "unknown")
    health_score = float(health_result.get("health_score", 0.0))
    mean_throughput = float(throughput_result.get("mean_throughput", 0.0))
    anomaly_status = anomaly_result.get("anomaly_status", "unknown")
    alert_count = int(alert_result.get("alert_count", 0))
    critical_count = int(alert_result.get("critical_count", 0))
    integration_status = integration_result.get("integration_status", "unknown")

    if (
        critical_count > 0
        or anomaly_status == "critical"
        or health_status == "critical"
    ):
        overall = "critical"
    elif (
        health_status == "degraded"
        or anomaly_status == "warning"
        or alert_count > 0
    ):
        overall = "degraded"
    elif integration_status in ("failed", "invalid_input"):
        overall = "offline"
    else:
        overall = "operational"

    return {
        "dashboard_valid": True,
        "health_status": health_status,
        "health_score": health_score,
        "mean_throughput": mean_throughput,
        "anomaly_status": anomaly_status,
        "alert_count": alert_count,
        "critical_count": critical_count,
        "integration_status": integration_status,
        "overall_operational_status": overall,
        "dashboard_status": "built",
    }


def summarize_dashboard(result: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(result, dict) or result.get("dashboard_valid") is not True:
        return {
            "summary_valid": False,
            "overall_operational_status": "invalid_input",
            "health_score": 0.0,
            "alert_count": 0,
        }

    return {
        "summary_valid": True,
        "overall_operational_status": result.get(
            "overall_operational_status", "invalid_input"
        ),
        "health_score": float(result.get("health_score", 0.0)),
        "alert_count": int(result.get("alert_count", 0)),
    }
