from typing import Any

def describe_adapter(adapter_config: Any, target_descriptor: Any, describer_config: Any) -> dict[str, Any]:
    if not isinstance(adapter_config, dict) or not isinstance(target_descriptor, dict):
        return {"adapter_description_status": "invalid_input"}
    adapter_id = adapter_config.get("adapter_id")
    adapter_kind = adapter_config.get("adapter_kind")
    if not adapter_id or not adapter_kind:
        return {"adapter_description_status": "invalid_input"}
    if not isinstance(adapter_id, str) or len(adapter_id) == 0:
        return {"adapter_description_status": "invalid_input"}
    if not isinstance(adapter_kind, str) or len(adapter_kind) == 0:
        return {"adapter_description_status": "invalid_input"}
    return {"adapter_description_status": "described", "adapter_id": adapter_id, "adapter_kind": adapter_kind}
