from typing import Any

def control_obs_plane(tap_rollup: Any, metric_rollup: Any, incident_rollup: Any, telemetry_rollup: Any) -> dict[str, Any]:
    if not isinstance(tap_rollup, dict) or not isinstance(metric_rollup, dict) or not isinstance(incident_rollup, dict) or not isinstance(telemetry_rollup, dict):
        return {"obs_cp_status": "not_operational"}
    tap_ok = tap_rollup.get("tap_rollup_status") == "rolled_up"
    met_ok = metric_rollup.get("metric_rollup_status") == "rolled_up"
    inc_ok = incident_rollup.get("incident_rollup_status") == "rolled_up"
    tel_ok = telemetry_rollup.get("telemetry_rollup_status") == "rolled_up"
    if not tap_ok or not met_ok or not inc_ok or not tel_ok:
        return {"obs_cp_status": "not_operational"}
    return {
        "obs_cp_status": "operational",
    }
