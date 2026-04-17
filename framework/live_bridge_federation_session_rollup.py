from typing import Any

def rollup_sessions(session_registry: dict[str, Any], session_index: dict[str, Any], session_broker: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(session_registry, dict) or not isinstance(session_index, dict) or not isinstance(session_broker, dict):
        return {"fed_session_rollup_status": "invalid_input"}
    r_ok = session_registry.get("session_registry_status") == "registered"
    i_ok = session_index.get("session_index_status") == "indexed"
    b_ok = session_broker.get("session_broker_status") == "brokered"
    all_complete = r_ok and i_ok and b_ok
    return {"fed_session_rollup_status": "rolled_up"} if all_complete else {"fed_session_rollup_status": "prerequisites_failed"}

