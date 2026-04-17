from typing import Any


def classify_orchestration_alerts(
    anomaly_result: dict[str, Any],
    escalation_result: dict[str, Any],
    failure_result: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(anomaly_result, dict)
        or not isinstance(escalation_result, dict)
        or not isinstance(failure_result, dict)
    ):
        return {
            "classification_valid": False,
            "alerts": [],
            "alert_count": 0,
            "critical_count": 0,
            "warning_count": 0,
            "classification_status": "invalid_input",
        }

    alerts = []

    if anomaly_result.get("anomaly_status") == "critical":
        alerts.append(
            {
                "alert_type": "anomaly_critical",
                "priority": "critical",
                "source": "anomaly_detector",
            }
        )

    if anomaly_result.get("anomaly_status") == "warning":
        alerts.append(
            {
                "alert_type": "anomaly_warning",
                "priority": "warning",
                "source": "anomaly_detector",
            }
        )

    if escalation_result.get("should_escalate") is True:
        alerts.append(
            {"alert_type": "escalation", "priority": "critical", "source": "escalation_router"}
        )

    if failure_result.get("action") == "abort":
        alerts.append(
            {
                "alert_type": "workflow_abort",
                "priority": "critical",
                "source": "failure_handler",
            }
        )

    if failure_result.get("action") == "escalate":
        alerts.append(
            {
                "alert_type": "workflow_escalate",
                "priority": "warning",
                "source": "failure_handler",
            }
        )

    critical_count = len([a for a in alerts if a.get("priority") == "critical"])
    warning_count = len([a for a in alerts if a.get("priority") == "warning"])

    return {
        "classification_valid": True,
        "alerts": alerts,
        "alert_count": len(alerts),
        "critical_count": critical_count,
        "warning_count": warning_count,
        "classification_status": "no_alerts" if len(alerts) == 0 else "classified",
    }


def summarize_alert_classification(result: dict[str, Any]) -> dict[str, Any]:
    if (
        not isinstance(result, dict)
        or result.get("classification_valid") is not True
    ):
        return {
            "summary_valid": False,
            "classification_status": "invalid_input",
            "alert_count": 0,
            "critical_count": 0,
        }

    return {
        "summary_valid": True,
        "classification_status": result.get("classification_status", "invalid_input"),
        "alert_count": int(result.get("alert_count", 0)),
        "critical_count": int(result.get("critical_count", 0)),
    }
