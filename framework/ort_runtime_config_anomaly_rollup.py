from typing import Any

def config_anomaly_rollup(input_dict):
    if not isinstance(input_dict, dict):
        return {"config_anomaly_rollup_status": "invalid"}
    return {"config_anomaly_rollup_status": "rolled_up"}
