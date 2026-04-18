from typing import Any

def build_anomaly_baseline(metric_flush: Any, baseline_config: Any) -> dict[str, Any]:
    if not isinstance(metric_flush, dict):
        return {"anomaly_baseline_building_status": "not_built"}
    flush_ok = metric_flush.get("metric_flush_status") == "flushed"
    if not flush_ok:
        return {"anomaly_baseline_building_status": "not_built"}
    return {
        "anomaly_baseline_building_status": "built",
        "baseline_mean": 0.0,
        "baseline_stddev": 0.0,
    }
