from typing import Any


def bridge_phase_telemetry(
    feedback: dict[str, Any],
    audit_log: dict[str, Any],
    target_sink: str,
) -> dict[str, Any]:
    if (
        not isinstance(feedback, dict)
        or not isinstance(audit_log, dict)
        or not isinstance(target_sink, str)
        or not target_sink
    ):
        return {
            "telemetry_status": "invalid_input",
            "bridged_events": 0,
            "sink": None,
        }

    feedback_status = feedback.get("feedback_status")
    event_count = audit_log.get("event_count", 0)

    if feedback_status != "collected":
        return {
            "telemetry_status": "no_feedback",
            "bridged_events": 0,
            "sink": None,
        }

    if event_count == 0:
        return {
            "telemetry_status": "empty_audit",
            "bridged_events": 0,
            "sink": None,
        }

    return {
        "telemetry_status": "bridged",
        "bridged_events": event_count,
        "sink": target_sink,
    }
