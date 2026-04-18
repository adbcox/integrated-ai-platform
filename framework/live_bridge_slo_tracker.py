from typing import Any

def track_slo(slo_descriptor: Any, metric_measurement: Any) -> dict[str, Any]:
    if not isinstance(slo_descriptor, dict) or not isinstance(metric_measurement, dict):
        return {"slo_tracking_status": "not_tracked"}
    desc_ok = slo_descriptor.get("slo_descriptor_status") == "described"
    if not desc_ok:
        return {"slo_tracking_status": "not_tracked"}
    return {
        "slo_tracking_status": "tracked",
        "current_pct": metric_measurement.get("measured_pct", 0.0),
    }
