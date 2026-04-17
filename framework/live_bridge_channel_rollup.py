from typing import Any
def rollup_channels(ingress: dict[str, Any], egress: dict[str, Any], bridge_reporter: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(ingress, dict) or not isinstance(egress, dict) or not isinstance(bridge_reporter, dict):
        return {"channel_rollup_status": "invalid_input", "rollup_channel_pair": None, "operations_complete": 0}
    all_complete = ingress.get("ingress_channel_status") == "built" and egress.get("egress_channel_status") == "built" and bridge_reporter.get("bridge_report_status") == "complete"
    if all_complete:
        return {"channel_rollup_status": "rolled_up", "rollup_channel_pair": (ingress.get("ingress_channel_id"), egress.get("egress_channel_id")), "operations_complete": 3}
    return {"channel_rollup_status": "incomplete_source", "rollup_channel_pair": None, "operations_complete": 0}
