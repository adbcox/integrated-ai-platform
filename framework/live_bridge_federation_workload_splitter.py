from typing import Any

def split_workload(affinity_routing: dict[str, Any], directory: dict[str, Any], split_config: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(affinity_routing, dict) or not isinstance(directory, dict) or not isinstance(split_config, dict):
        return {"workload_split_status": "invalid_input", "split_count": 0}
    a_ok = affinity_routing.get("affinity_routing_status") == "routed"
    d_ok = directory.get("directory_status") == "built"
    peer_count = directory.get("directory_peer_count", 0)
    if not a_ok or not d_ok or peer_count <= 0:
        return {"workload_split_status": "prerequisites_failed", "split_count": 0}
    return {"workload_split_status": "split", "split_count": peer_count}

