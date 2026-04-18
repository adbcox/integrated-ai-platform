from typing import Any

def runtime_forensics_anomaly_rollup(input_dict):
    if not isinstance(input_dict, dict):
        return {"runtime_forensics_anomaly_rollup_status": "invalid"}
    return {"runtime_forensics_anomaly_rollup_status": "ok"}
