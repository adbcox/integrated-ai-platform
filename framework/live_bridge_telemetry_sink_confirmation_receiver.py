from typing import Any

def receive_telemetry_sink_confirmation(telemetry_sink_publication: Any, confirmation_data: Any) -> dict[str, Any]:
    if not isinstance(telemetry_sink_publication, dict):
        return {"telemetry_sink_confirmation_receipt_status": "not_received"}
    pub_ok = telemetry_sink_publication.get("telemetry_sink_publication_status") == "published"
    if not pub_ok:
        return {"telemetry_sink_confirmation_receipt_status": "not_received"}
    return {
        "telemetry_sink_confirmation_receipt_status": "received",
        "confirmation_count": confirmation_data.get("confirmation_count", 0),
    }
