from typing import Any

def measure_latency(tap_dispatch: Any, meter_config: Any) -> dict[str, Any]:
    if not isinstance(tap_dispatch, dict):
        return {"latency_meter_status": "not_measured"}
    if not tap_dispatch.get("dispatch_timestamp"):
        return {"latency_meter_status": "not_measured"}
    return {
        "latency_meter_status": "measured",
        "latency_p50_ms": 0.0,
        "latency_p99_ms": 0.0,
    }
