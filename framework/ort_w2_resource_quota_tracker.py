from typing import Any

def resource_quota_tracker(input_dict):
    if not isinstance(input_dict, dict):
        return {"resource_quota_tracker_status": "invalid"}
    return {"resource_quota_tracker_status": "ok"}
