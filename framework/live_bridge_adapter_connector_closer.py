from typing import Any

def close_connector(connector: Any, closure_reason: Any, closer_config: Any) -> dict[str, Any]:
    if not isinstance(connector, dict):
        return {"connector_close_status": "failed"}
    c_ok = connector.get("connector_open_status") == "open"
    if not c_ok:
        return {"connector_close_status": "failed"}
    reason = closure_reason.get("reason", "normal") if isinstance(closure_reason, dict) else "normal"
    return {
        "connector_close_status": "closed",
        "adapter_id": connector.get("adapter_id"),
        "closure_reason": reason,
    }
