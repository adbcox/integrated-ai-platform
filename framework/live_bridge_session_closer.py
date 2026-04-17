from typing import Any
def close_session(session: dict[str, Any], closure_reason: dict[str, Any], closer_config: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(session, dict) or not isinstance(closure_reason, dict) or not isinstance(closer_config, dict):
        return {"session_close_status": "invalid_input", "closed_session_id": None, "close_reason": None}
    s_ok = session.get("session_status") == "opened"
    r_ok = bool(closure_reason.get("reason"))
    if s_ok and r_ok:
        return {"session_close_status": "closed", "closed_session_id": session.get("session_id"), "close_reason": closure_reason.get("reason")}
    return {"session_close_status": "not_opened" if not s_ok else "no_reason", "closed_session_id": None, "close_reason": None}
