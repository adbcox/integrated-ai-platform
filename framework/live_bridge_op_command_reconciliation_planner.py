from typing import Any
def plan_command_reconciliation(plan_input):
    if not isinstance(plan_input, dict): return {"op_reconciliation_plan_status": "invalid"}
    if "reconciliation_id" not in plan_input: return {"op_reconciliation_plan_status": "invalid"}
    return {"op_reconciliation_plan_status": "planned", "reconciliation_id": plan_input.get("reconciliation_id")}
