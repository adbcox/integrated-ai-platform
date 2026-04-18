from typing import Any

def report_adapter_layer(validation: Any, audit: Any, phase_id: Any) -> dict[str, Any]:
    if not isinstance(validation, dict) or not isinstance(audit, dict):
        return {"adapter_layer_report_status": "failed"}
    v_ok = validation.get("adapter_validation_status") == "valid"
    a_ok = audit.get("adapter_layer_audit_status") == "passed"
    if not v_ok or not a_ok:
        return {"adapter_layer_report_status": "failed"}
    return {
        "adapter_layer_report_status": "reported",
        "phase_id": phase_id,
        "validation_status": "valid",
    }
