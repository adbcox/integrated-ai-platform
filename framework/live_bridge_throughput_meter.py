from typing import Any

def measure_throughput(metric_flush: Any, meter_config: Any) -> dict[str, Any]:
    if not isinstance(metric_flush, dict):
        return {"throughput_meter_status": "not_measured"}
    flush_ok = metric_flush.get("metric_flush_status") == "flushed"
    if not flush_ok:
        return {"throughput_meter_status": "not_measured"}
    return {
        "throughput_meter_status": "measured",
        "throughput_eps": 0.0,
    }
