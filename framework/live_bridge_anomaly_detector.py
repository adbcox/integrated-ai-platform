from typing import Any

def detect_anomaly(anomaly_baseline: Any, metric_measurement: Any) -> dict[str, Any]:
    if not isinstance(anomaly_baseline, dict) or not isinstance(metric_measurement, dict):
        return {"anomaly_detection_status": "not_detected"}
    baseline_ok = anomaly_baseline.get("anomaly_baseline_building_status") == "built"
    if not baseline_ok:
        return {"anomaly_detection_status": "not_detected"}
    return {
        "anomaly_detection_status": "detected",
        "is_anomaly": False,
        "anomaly_score": 0.0,
    }
