from typing import Any

def detect_federation_anomaly(fed_health: dict[str, Any], conflict: dict[str, Any], clock_alignment: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(fed_health, dict) or not isinstance(conflict, dict) or not isinstance(clock_alignment, dict):
        return {"fed_anomaly_status": "invalid_input"}
    health_ok = fed_health.get("fed_health_status") == "green"
    no_conflict = conflict.get("conflict_status") == "none"
    clock_ok = clock_alignment.get("clock_alignment_status") == "aligned"
    if not health_ok or not no_conflict or not clock_ok:
        return {"fed_anomaly_status": "detected"}
    return {"fed_anomaly_status": "none"}

