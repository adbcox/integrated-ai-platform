from typing import Any

def index_sessions(session_registry: dict[str, Any], index_config: dict[str, Any], index_state: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(session_registry, dict) or not isinstance(index_config, dict) or not isinstance(index_state, dict):
        return {"session_index_status": "invalid_input", "indexed_count": 0}
    s_ok = session_registry.get("session_registry_status") == "registered"
    indexed_count = index_config.get("index_size", 1) if s_ok else 0
    return {"session_index_status": "indexed", "indexed_count": indexed_count} if s_ok else {"session_index_status": "registry_not_registered", "indexed_count": 0}

