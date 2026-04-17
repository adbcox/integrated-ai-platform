from typing import Any

def broadcast_operation(ownership: dict[str, Any], directory: dict[str, Any], broadcaster_config: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(ownership, dict) or not isinstance(directory, dict) or not isinstance(broadcaster_config, dict):
        return {"broadcast_status": "invalid_input", "broadcast_id": None}
    o_ok = ownership.get("ownership_status") == "arbitrated"
    d_ok = directory.get("directory_status") == "built"
    return {"broadcast_status": "broadcast", "broadcast_id": broadcaster_config.get("broadcast_id", "bcast-0001")} if o_ok and d_ok else {"broadcast_status": "prerequisites_failed", "broadcast_id": None}

