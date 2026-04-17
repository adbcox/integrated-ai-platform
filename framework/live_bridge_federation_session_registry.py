from typing import Any

def register_session(session_validation: dict[str, Any], directory: dict[str, Any], registry_config: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(session_validation, dict) or not isinstance(directory, dict) or not isinstance(registry_config, dict):
        return {"session_registry_status": "invalid_input", "registry_session_count": 0}
    s_ok = session_validation.get("session_validation_status") == "valid"
    d_ok = directory.get("directory_status") == "built"
    if not s_ok:
        return {"session_registry_status": "session_not_valid", "registry_session_count": 0}
    return {"session_registry_status": "registered", "registry_session_count": registry_config.get("session_count", 1)} if s_ok and d_ok else {"session_registry_status": "directory_not_built", "registry_session_count": 0}

