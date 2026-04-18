from typing import Any
def execute_command_reconciliation(exec_input):
    if not isinstance(exec_input, dict): return {"op_reconciliation_execute_status": "invalid"}
    if exec_input.get("op_reconciliation_plan_status") != "planned": return {"op_reconciliation_execute_status": "invalid"}
    return {"op_reconciliation_execute_status": "executed", "reconciliation_id": exec_input.get("reconciliation_id")}
