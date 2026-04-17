from typing import Any
def open_session(ingress: dict[str, Any], egress: dict[str, Any], session_config: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(ingress, dict) or not isinstance(egress, dict) or not isinstance(session_config, dict):
        return {"session_status": "invalid_input", "session_env_id": None, "session_id": None}
    i_ok = ingress.get("ingress_channel_status") == "built"
    e_ok = egress.get("egress_channel_status") == "built"
    if i_ok and e_ok:
        return {"session_status": "opened", "session_env_id": ingress.get("ingress_env_id"), "session_id": session_config.get("session_id", "sess-0001")}
    return {"session_status": "no_ingress" if not i_ok else "no_egress", "session_env_id": None, "session_id": None}
