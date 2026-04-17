from typing import Any

def resume_cycle(pause: dict[str, Any], cycle_health: dict[str, Any], resume_config: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(pause, dict) or not isinstance(cycle_health, dict) or not isinstance(resume_config, dict):
        return {"resume_status": "invalid_input", "resumed_env_id": None, "resume_token": None}
    p_paused = pause.get("pause_status") == "paused"
    h_green = cycle_health.get("cycle_health_watch_status") == "green"
    if not p_paused:
        return {"resume_status": "not_paused", "resumed_env_id": None, "resume_token": None}
    if p_paused and not h_green:
        return {"resume_status": "unhealthy", "resumed_env_id": None, "resume_token": None}
    return {"resume_status": "resumed", "resumed_env_id": pause.get("paused_env_id"), "resume_token": resume_config.get("token", "res-0001")} if p_paused and h_green else {"resume_status": "invalid_input", "resumed_env_id": None, "resume_token": None}
