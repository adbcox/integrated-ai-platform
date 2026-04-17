from typing import Any

def execute_reconciliation(plan: dict[str, Any], governance_cp: dict[str, Any], executor_config: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(plan, dict) or not isinstance(governance_cp, dict) or not isinstance(executor_config, dict):
        return {"reconciliation_execution_status": "invalid_input", "executed_operation_id": None, "reconciliation_outcome": None}
    p_ok = plan.get("reconciliation_plan_status") == "planned"
    g_op = governance_cp.get("governance_cp_status") == "operational"
    if not p_ok:
        return {"reconciliation_execution_status": "no_plan", "executed_operation_id": None, "reconciliation_outcome": None}
    if p_ok and not g_op:
        return {"reconciliation_execution_status": "governance_offline", "executed_operation_id": None, "reconciliation_outcome": None}
    return {"reconciliation_execution_status": "executed", "executed_operation_id": plan.get("reconciliation_operation_id"), "reconciliation_outcome": executor_config.get("outcome", "match")} if p_ok and g_op else {"reconciliation_execution_status": "invalid_input", "executed_operation_id": None, "reconciliation_outcome": None}
