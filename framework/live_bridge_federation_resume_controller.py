from typing import Any

def resume_federation(fed_pause: dict[str, Any], fed_health: dict[str, Any], resume_config: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(fed_pause, dict) or not isinstance(fed_health, dict) or not isinstance(resume_config, dict):
        return {"fed_resume_status": "invalid_input"}
    p_ok = fed_pause.get("fed_pause_status") == "paused"
    h_ok = fed_health.get("fed_health_status") == "green"
    if not h_ok:
        return {"fed_resume_status": "health_not_green"}
    return {"fed_resume_status": "resumed"} if p_ok and h_ok else {"fed_resume_status": "not_paused"}

