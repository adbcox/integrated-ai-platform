from typing import Any

def execute_adapter_reconciliation(plan: Any, fed_gov_cp: Any, executor_config: Any) -> dict[str, Any]:
    if not isinstance(plan, dict) or not isinstance(fed_gov_cp, dict):
        return {"adapter_reconciliation_execution_status": "failed"}
    p_ok = plan.get("adapter_reconciliation_plan_status") == "planned"
    f_ok = fed_gov_cp.get("fed_gov_cp_status") == "operational"
    if not p_ok or not f_ok:
        return {"adapter_reconciliation_execution_status": "failed"}
    return {
        "adapter_reconciliation_execution_status": "executed",
        "adapter_id": plan.get("adapter_id"),
    }
