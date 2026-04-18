from typing import Any

def open_connector(directive_binding: Any, egress_channel: Any, opener_config: Any) -> dict[str, Any]:
    if not isinstance(directive_binding, dict) or not isinstance(egress_channel, dict):
        return {"connector_open_status": "failed"}
    d_ok = directive_binding.get("directive_binding_status") == "bound"
    e_ok = egress_channel.get("egress_channel_status") == "built"
    if not d_ok or not e_ok:
        return {"connector_open_status": "failed"}
    return {
        "connector_open_status": "open",
        "adapter_id": directive_binding.get("adapter_id"),
        "channel_type": egress_channel.get("channel_type"),
    }
