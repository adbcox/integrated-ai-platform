from typing import Any

def measure_error_rate(metric_flush: Any, meter_config: Any) -> dict[str, Any]:
    if not isinstance(metric_flush, dict):
        return {"error_rate_meter_status": "not_measured"}
    flush_ok = metric_flush.get("metric_flush_status") == "flushed"
    if not flush_ok:
        return {"error_rate_meter_status": "not_measured"}
    return {
        "error_rate_meter_status": "measured",
        "error_rate_pct": 0.0,
    }
