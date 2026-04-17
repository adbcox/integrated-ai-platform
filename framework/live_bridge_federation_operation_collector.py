from typing import Any

def collect_operation_results(broadcast: dict[str, Any], peer_results: dict[str, Any], collector_config: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(broadcast, dict) or not isinstance(peer_results, dict) or not isinstance(collector_config, dict):
        return {"collection_status": "invalid_input", "collected_count": 0}
    b_ok = broadcast.get("broadcast_status") == "broadcast"
    result_count = peer_results.get("result_count", 0)
    if not b_ok or result_count <= 0:
        return {"collection_status": "no_results", "collected_count": 0}
    return {"collection_status": "collected", "collected_count": result_count}

