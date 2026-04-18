from typing import Any

def gate_tap_attachment(tap_registration: Any) -> dict[str, Any]:
    if not isinstance(tap_registration, dict):
        return {"tap_attachment_gate_status": "closed"}
    reg_ok = tap_registration.get("tap_registration_status") == "registered"
    if not reg_ok:
        return {"tap_attachment_gate_status": "closed"}
    return {
        "tap_attachment_gate_status": "open",
    }
