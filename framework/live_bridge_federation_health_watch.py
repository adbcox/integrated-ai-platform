from typing import Any

def watch_federation_health(cycle_health: dict[str, Any], peer_health_report: dict[str, Any], watch_config: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(cycle_health, dict) or not isinstance(peer_health_report, dict) or not isinstance(watch_config, dict):
        return {"fed_health_status": "invalid_input"}
    c_ok = cycle_health.get("cycle_health_watch_status") == "green"
    p_ok = peer_health_report.get("peer_health") == "green"
    if not c_ok:
        return {"fed_health_status": "cycle_not_green"}
    return {"fed_health_status": "green"} if c_ok and p_ok else {"fed_health_status": "peer_degraded"}

