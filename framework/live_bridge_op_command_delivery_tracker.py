from typing import Any
def track_command_delivery(tracker_input):
    if not isinstance(tracker_input, dict): return {"op_delivery_track_status": "invalid"}
    if "delivery_id" not in tracker_input: return {"op_delivery_track_status": "invalid"}
    return {"op_delivery_track_status": "tracked", "delivery_id": tracker_input.get("delivery_id")}
