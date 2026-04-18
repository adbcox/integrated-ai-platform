from typing import Any

def config_snapshot_builder(input_dict):
    if not isinstance(input_dict, dict):
        return {"config_snapshot_status": "invalid"}
    return {"config_snapshot_status": "snapshotted"}
