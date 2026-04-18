from typing import Any

def watch_obs_health(obs_cp: Any, supervisory_health: Any) -> dict[str, Any]:
    if not isinstance(obs_cp, dict) or not isinstance(supervisory_health, dict):
        return {"obs_health_status": "red"}
    cp_ok = obs_cp.get("obs_cp_status") == "operational"
    sh_ok = supervisory_health.get("supervisory_health_status") == "green"
    if not cp_ok or not sh_ok:
        return {"obs_health_status": "red"}
    return {
        "obs_health_status": "green",
    }
