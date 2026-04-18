from typing import Any
def detect_audit_anomaly(detector_input):
    if not isinstance(detector_input, dict): return {"op_audit_anomaly_detection_status": "invalid"}
    if "detection_id" not in detector_input: return {"op_audit_anomaly_detection_status": "invalid"}
    return {"op_audit_anomaly_detection_status": "detected", "detection_id": detector_input.get("detection_id")}
