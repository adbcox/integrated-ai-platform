from typing import Any

def handshake_peer(membership: dict[str, Any], peer_descriptor: dict[str, Any], handshake_config: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(membership, dict) or not isinstance(peer_descriptor, dict) or not isinstance(handshake_config, dict):
        return {"peer_handshake_status": "invalid_input", "peer_id": None, "peer_env_id": None}
    m_ok = membership.get("membership_status") == "registered"
    p_ok = "peer_id" in peer_descriptor and "peer_env_id" in peer_descriptor
    if not m_ok:
        return {"peer_handshake_status": "not_member", "peer_id": None, "peer_env_id": None}
    return {"peer_handshake_status": "shaken", "peer_id": peer_descriptor.get("peer_id"), "peer_env_id": peer_descriptor.get("peer_env_id")} if m_ok and p_ok else {"peer_handshake_status": "invalid_descriptor", "peer_id": None, "peer_env_id": None}

