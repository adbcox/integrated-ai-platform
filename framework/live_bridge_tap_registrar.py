from typing import Any

def register_tap(tap_descriptor: Any, adapter_seal: Any) -> dict[str, Any]:
    if not isinstance(tap_descriptor, dict) or not isinstance(adapter_seal, dict):
        return {"tap_registration_status": "not_registered"}
    d_ok = tap_descriptor.get("tap_descriptor_status") == "described"
    seal_ok = adapter_seal.get("adapter_layer_seal_status") == "sealed"
    if not d_ok or not seal_ok:
        return {"tap_registration_status": "not_registered"}
    return {
        "tap_registration_status": "registered",
    }
