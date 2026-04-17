from typing import Any

def broker_session(session_index: dict[str, Any], peer_validation: dict[str, Any], broker_config: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(session_index, dict) or not isinstance(peer_validation, dict) or not isinstance(broker_config, dict):
        return {"session_broker_status": "invalid_input", "brokered_session_id": None}
    s_ok = session_index.get("session_index_status") == "indexed"
    p_ok = peer_validation.get("peer_validation_status") == "valid"
    if not p_ok:
        return {"session_broker_status": "peer_not_valid", "brokered_session_id": None}
    return {"session_broker_status": "brokered", "brokered_session_id": broker_config.get("session_id", "ses-0001")} if s_ok and p_ok else {"session_broker_status": "index_not_ready", "brokered_session_id": None}

