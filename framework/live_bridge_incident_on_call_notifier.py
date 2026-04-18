from typing import Any

def notify_on_call(incident_triage_routing: Any, notification_config: Any) -> dict[str, Any]:
    if not isinstance(incident_triage_routing, dict):
        return {"incident_on_call_notification_status": "not_sent"}
    route_ok = incident_triage_routing.get("incident_triage_routing_status") == "routed"
    if not route_ok:
        return {"incident_on_call_notification_status": "not_sent"}
    return {
        "incident_on_call_notification_status": "sent",
        "notification_sent_timestamp": "0",
    }
