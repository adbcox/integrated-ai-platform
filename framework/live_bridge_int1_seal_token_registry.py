from typing import Any

def get_seal_token_registry() -> dict[str, Any]:
    registry = {
        "LOB-W1": {
            "seal_function": "complete_handshake",
            "seal_key": "handshake_status",
            "seal_success_value": "completed",
            "seal_module": "framework.live_bridge_handshake_completer",
        },
        "LOB-W2": {
            "seal_function": "report_cycle_completion",
            "seal_key": "cycle_completion_report_status",
            "seal_success_value": "complete",
            "seal_module": "framework.live_bridge_cycle_completion_reporter",
        },
        "LOB-W3": {
            "seal_function": "seal_federation_handshake",
            "seal_key": "fed_seal_status",
            "seal_success_value": "sealed",
            "seal_module": "framework.live_bridge_federation_handshake_sealer",
        },
    }
    required_keys = {"seal_function", "seal_key", "seal_success_value", "seal_module"}
    all_valid = True
    seal_count = 0
    for package_key, entry in registry.items():
        if not isinstance(entry, dict):
            all_valid = False
            break
        if set(entry.keys()) != required_keys:
            all_valid = False
            break
        for k, v in entry.items():
            if not isinstance(v, str) or len(v) == 0:
                all_valid = False
                break
        if not all_valid:
            break
        seal_count += 1
    if all_valid and seal_count == 3:
        result = {"registry_status": "built", "seal_token_count": seal_count}
        result.update(registry)
        return result
    return {"registry_status": "invalid", "seal_token_count": 0}

