from typing import Any

def validate_peer(peer_handshake: dict[str, Any], governance_cp: dict[str, Any], validator_config: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(peer_handshake, dict) or not isinstance(governance_cp, dict) or not isinstance(validator_config, dict):
        return {"peer_validation_status": "invalid_input", "validated_peer_id": None}
    p_ok = peer_handshake.get("peer_handshake_status") == "shaken"
    g_ok = governance_cp.get("governance_cp_status") == "operational"
    if not g_ok:
        return {"peer_validation_status": "governance_offline", "validated_peer_id": None}
    return {"peer_validation_status": "valid", "validated_peer_id": peer_handshake.get("peer_id")} if p_ok and g_ok else {"peer_validation_status": "handshake_failed", "validated_peer_id": None}

