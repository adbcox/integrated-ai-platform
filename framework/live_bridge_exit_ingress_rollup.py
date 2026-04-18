from typing import Any
def rollup_exit_ingress(rollup_input):
    if not isinstance(rollup_input, dict): return {"exit_ingress_rollup_status": "invalid"}
    if "rollup_id" not in rollup_input: return {"exit_ingress_rollup_status": "invalid"}
    return {"exit_ingress_rollup_status": "rolled_up", "rollup_id": rollup_input.get("rollup_id")}
