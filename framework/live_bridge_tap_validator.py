from typing import Any

def validate_tap(tap_attachment_gate: Any) -> dict[str, Any]:
    if not isinstance(tap_attachment_gate, dict):
        return {"tap_validation_status": "not_validated"}
    gate_ok = tap_attachment_gate.get("tap_attachment_gate_status") == "open"
    if not gate_ok:
        return {"tap_validation_status": "not_validated"}
    return {
        "tap_validation_status": "valid",
    }
