from typing import Any

def rollup_peers(peer_handshake: dict[str, Any], peer_validation: dict[str, Any], directory: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(peer_handshake, dict) or not isinstance(peer_validation, dict) or not isinstance(directory, dict):
        return {"fed_peer_rollup_status": "invalid_input"}
    h_ok = peer_handshake.get("peer_handshake_status") == "shaken"
    v_ok = peer_validation.get("peer_validation_status") == "valid"
    d_ok = directory.get("directory_status") == "built"
    all_complete = h_ok and v_ok and d_ok
    return {"fed_peer_rollup_status": "rolled_up"} if all_complete else {"fed_peer_rollup_status": "prerequisites_failed"}

