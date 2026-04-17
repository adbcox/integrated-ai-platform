from typing import Any

def build_federation_directory(peer_validation: dict[str, Any], membership: dict[str, Any], directory_config: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(peer_validation, dict) or not isinstance(membership, dict) or not isinstance(directory_config, dict):
        return {"directory_status": "invalid_input", "directory_id": None, "directory_peer_count": 0}
    p_ok = peer_validation.get("peer_validation_status") == "valid"
    m_ok = membership.get("membership_status") == "registered"
    peer_count = directory_config.get("peer_count", 1) if (p_ok and m_ok) else 0
    return {"directory_status": "built", "directory_id": directory_config.get("directory_id", "dir-0001"), "directory_peer_count": peer_count} if p_ok and m_ok else {"directory_status": "prerequisites_failed", "directory_id": None, "directory_peer_count": 0}

