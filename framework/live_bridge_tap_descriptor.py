from typing import Any

def describe_tap(tap_config: Any) -> dict[str, Any]:
    if not isinstance(tap_config, dict):
        return {"tap_descriptor_status": "not_described"}
    if not tap_config.get("tap_id"):
        return {"tap_descriptor_status": "not_described"}
    return {
        "tap_descriptor_status": "described",
        "tap_id": tap_config.get("tap_id"),
    }
