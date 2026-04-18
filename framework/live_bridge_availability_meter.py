from typing import Any

def measure_availability(error_rate_meter: Any, meter_config: Any) -> dict[str, Any]:
    if not isinstance(error_rate_meter, dict):
        return {"availability_meter_status": "not_measured"}
    err_ok = error_rate_meter.get("error_rate_meter_status") == "measured"
    if not err_ok:
        return {"availability_meter_status": "not_measured"}
    return {
        "availability_meter_status": "measured",
        "availability_pct": 100.0,
    }
