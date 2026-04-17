from typing import Any
def monitor_bridge_health(bridge_cp: dict[str, Any], bridge_audit: dict[str, Any], health_config: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(bridge_cp, dict) or not isinstance(bridge_audit, dict) or not isinstance(health_config, dict):
        return {"bridge_health_status": "invalid_input", "health_env_id": None, "health_level": None}
    cp_ok = bridge_cp.get("bridge_cp_status") == "operational"
    audit_ok = bridge_audit.get("bridge_audit_status") in ("passed", "degraded")
    if cp_ok and audit_ok:
        return {"bridge_health_status": "healthy", "health_env_id": bridge_cp.get("bridge_cp_env_id"), "health_level": "green"}
    if cp_ok and not audit_ok:
        return {"bridge_health_status": "degraded", "health_env_id": None, "health_level": "yellow"}
    return {"bridge_health_status": "critical", "health_env_id": None, "health_level": "red"}
