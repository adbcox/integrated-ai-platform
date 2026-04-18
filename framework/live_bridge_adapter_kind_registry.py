from typing import Any

def get_adapter_kind_registry() -> dict[str, Any]:
    registry = {
        "webhook": {"kind_id": "webhook", "connector_type": "http"},
        "message_bus": {"kind_id": "message_bus", "connector_type": "queue"},
        "storage_sink": {"kind_id": "storage_sink", "connector_type": "storage"},
        "peer_service": {"kind_id": "peer_service", "connector_type": "rpc"},
        "log_stream": {"kind_id": "log_stream", "connector_type": "stream"},
    }
    all_valid = True
    kind_count = 0
    for kind_id, entry in registry.items():
        if not isinstance(entry, dict):
            all_valid = False
            break
        if "kind_id" not in entry or "connector_type" not in entry:
            all_valid = False
            break
        for k, v in entry.items():
            if not isinstance(v, str) or len(v) == 0:
                all_valid = False
                break
        if not all_valid:
            break
        kind_count += 1
    if all_valid and kind_count == 5:
        result = {"registry_status": "built", "kind_count": kind_count}
        result.update(registry)
        return result
    return {"registry_status": "invalid", "kind_count": 0}
