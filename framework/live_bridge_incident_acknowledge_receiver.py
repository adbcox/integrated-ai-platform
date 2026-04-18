from typing import Any

def receive_incident_acknowledgement(incident_on_call_notification: Any, ack_data: Any) -> dict[str, Any]:
    if not isinstance(incident_on_call_notification, dict):
        return {"incident_acknowledgement_receipt_status": "not_received"}
    notif_ok = incident_on_call_notification.get("incident_on_call_notification_status") == "sent"
    if not notif_ok:
        return {"incident_acknowledgement_receipt_status": "not_received"}
    if not ack_data.get("ack_received"):
        return {"incident_acknowledgement_receipt_status": "not_received"}
    return {
        "incident_acknowledgement_receipt_status": "received",
        "ack_timestamp": ack_data.get("ack_timestamp", "0"),
    }
