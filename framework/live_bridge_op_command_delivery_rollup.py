from typing import Any
def rollup_command_delivery(rollup_input):
    if not isinstance(rollup_input, dict): return {"op_delivery_rollup_status": "invalid"}
    if rollup_input.get("op_delivery_validation_status") != "valid": return {"op_delivery_rollup_status": "invalid"}
    return {"op_delivery_rollup_status": "rolled_up", "delivery_id": rollup_input.get("delivery_id")}
