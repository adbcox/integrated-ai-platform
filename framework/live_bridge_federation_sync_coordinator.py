from typing import Any

def coordinate_sync(clock_alignment: dict[str, Any], directory: dict[str, Any], sync_config: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(clock_alignment, dict) or not isinstance(directory, dict) or not isinstance(sync_config, dict):
        return {"sync_status": "invalid_input", "synced_peer_count": 0}
    c_ok = clock_alignment.get("clock_alignment_status") == "aligned"
    d_ok = directory.get("directory_status") == "built"
    if not c_ok:
        return {"sync_status": "clock_not_aligned", "synced_peer_count": 0}
    peer_count = directory.get("directory_peer_count", 0)
    return {"sync_status": "synced", "synced_peer_count": peer_count} if c_ok and d_ok else {"sync_status": "directory_not_built", "synced_peer_count": 0}

