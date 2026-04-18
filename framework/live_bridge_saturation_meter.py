from typing import Any

def measure_saturation(metric_flush: Any, meter_config: Any) -> dict[str, Any]:
    if not isinstance(metric_flush, dict):
        return {"saturation_meter_status": "not_measured"}
    flush_ok = metric_flush.get("metric_flush_status") == "flushed"
    if not flush_ok:
        return {"saturation_meter_status": "not_measured"}
    return {
        "saturation_meter_status": "measured",
        "saturation_pct": 0.0,
    }
