from typing import Any
def validate_session(session: dict[str, Any], guard: dict[str, Any], validator_config: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(session, dict) or not isinstance(guard, dict) or not isinstance(validator_config, dict):
        return {"session_validation_status": "invalid_input", "validated_session_id": None, "validated_env_id": None}
    s_ok = session.get("session_status") == "opened"
    g_ok = guard.get("boundary_guard_status") == "armed"
    if s_ok and g_ok:
        return {"session_validation_status": "valid", "validated_session_id": session.get("session_id"), "validated_env_id": session.get("session_env_id")}
    return {"session_validation_status": "not_opened" if not s_ok else "not_armed", "validated_session_id": None, "validated_env_id": None}
