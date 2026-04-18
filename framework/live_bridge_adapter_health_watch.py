from typing import Any

def watch_adapter_health(adapter_cp: Any, supervisory_health: Any, watch_config: Any) -> dict[str, Any]:
    if not isinstance(adapter_cp, dict) or not isinstance(supervisory_health, dict):
        return {"adapter_health_status": "red"}
    cp_ok = adapter_cp.get("adapter_cp_status") == "operational"
    sh_ok = supervisory_health.get("supervisory_health_status") == "green"
    if not cp_ok or not sh_ok:
        return {"adapter_health_status": "red"}
    return {
        "adapter_health_status": "green",
        "adapter_cp_status": "operational",
    }
