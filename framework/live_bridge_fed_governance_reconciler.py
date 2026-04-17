from typing import Any

def reconcile_governance(intervention: dict, fed_ledger: dict, reconciler_config: dict) -> dict:
    if not isinstance(intervention, dict) or not isinstance(fed_ledger, dict) or not isinstance(reconciler_config, dict):
        return {"fed_gov_reconciliation_status": "invalid_input"}
    i_ok = intervention.get("intervention_execution_status") == "executed"
    l_ok = fed_ledger.get("fed_ledger_status") == "written"
    if not i_ok:
        return {"fed_gov_reconciliation_status": "no_intervention"}
    if not l_ok:
        return {"fed_gov_reconciliation_status": "no_ledger"}
    return {
        "fed_gov_reconciliation_status": "reconciled",
        "reconciled_directive_id": intervention.get("executed_directive_id"),
        "reconciled_ledger_op_id": fed_ledger.get("fed_ledger_operation_id"),
        "reconciliation_outcome": reconciler_config.get("outcome", "merged"),
    }
