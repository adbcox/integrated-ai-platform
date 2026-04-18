from typing import Any
def rollup_command_anomaly(rollup_input):
    if not isinstance(rollup_input, dict): return {"op_anomaly_rollup_status": "invalid"}
    if rollup_input.get("op_anomaly_classification_status") != "classified": return {"op_anomaly_rollup_status": "invalid"}
    return {"op_anomaly_rollup_status": "rolled_up", "detection_id": rollup_input.get("detection_id")}
