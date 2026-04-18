from typing import Any

def dispatch_via_adapter(connector_validation: Any, payload_validation: Any, dispatcher_config: Any) -> dict[str, Any]:
    if not isinstance(connector_validation, dict) or not isinstance(payload_validation, dict):
        return {"adapter_dispatch_status": "failed"}
    c_ok = connector_validation.get("connector_validation_status") == "valid"
    p_ok = payload_validation.get("payload_validation_status") == "valid"
    if not c_ok or not p_ok:
        return {"adapter_dispatch_status": "failed"}
    return {
        "adapter_dispatch_status": "dispatched",
        "schema_id": payload_validation.get("schema_id"),
        "adapter_id": connector_validation.get("adapter_id"),
    }
