from typing import Any
def track_exit_quota(tracker_input):
    if not isinstance(tracker_input, dict): return {"exit_quota_track_status": "invalid"}
    if "quota_id" not in tracker_input: return {"exit_quota_track_status": "invalid"}
    return {"exit_quota_track_status": "tracked", "quota_id": tracker_input.get("quota_id")}
