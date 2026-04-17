from typing import Any

def detect_execution_anomalies(
    jobs: list[dict[str, Any]],
    events: list[dict[str, Any]],
) -> dict[str, Any]:
    anomalies = []
    if not jobs or not events:
        return {
            "anomaly_count": 0,
            "anomalies": [],
        }
    retry_events = [e for e in events if isinstance(e, dict) and e.get("event_type") == "retry_triggered"]
    if len(retry_events) > len(jobs) * 0.3:
        anomalies.append({
            "type": "high_retry_rate",
            "severity": "medium",
            "detail": "Retry rate {:.1%} exceeds threshold".format(len(retry_events) / float(len(jobs))),
        })
    escalation_events = [e for e in events if isinstance(e, dict) and e.get("event_type") == "escalated"]
    if len(escalation_events) > len(jobs) * 0.2:
        anomalies.append({
            "type": "high_escalation_rate",
            "severity": "high",
            "detail": "Escalation rate {:.1%} exceeds threshold".format(len(escalation_events) / float(len(jobs))),
        })
    return {
        "anomaly_count": len(anomalies),
        "anomalies": anomalies,
    }
