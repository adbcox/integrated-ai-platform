from typing import Any

def classify_anomaly(anomaly_detection: Any, classifier_config: Any) -> dict[str, Any]:
    if not isinstance(anomaly_detection, dict):
        return {"anomaly_classification_status": "not_classified"}
    detect_ok = anomaly_detection.get("anomaly_detection_status") == "detected"
    if not detect_ok:
        return {"anomaly_classification_status": "not_classified"}
    is_anomaly = anomaly_detection.get("is_anomaly", False)
    return {
        "anomaly_classification_status": "classified",
        "anomaly_class": "normal" if not is_anomaly else "degradation",
    }
