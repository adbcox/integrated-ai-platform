from typing import Any
def classify_audit_anomaly(classifier_input):
    if not isinstance(classifier_input, dict): return {"op_audit_anomaly_classification_status": "invalid"}
    if classifier_input.get("op_audit_anomaly_detection_status") != "detected": return {"op_audit_anomaly_classification_status": "invalid"}
    return {"op_audit_anomaly_classification_status": "classified", "detection_id": classifier_input.get("detection_id")}
