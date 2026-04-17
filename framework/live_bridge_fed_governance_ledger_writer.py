from typing import Any

def write_fed_gov_ledger(reconciliation: dict, intervention: dict, ledger_config: dict) -> dict:
    if not isinstance(reconciliation, dict) or not isinstance(intervention, dict) or not isinstance(ledger_config, dict):
        return {"fed_gov_ledger_status": "invalid_input"}
    r_ok = reconciliation.get("fed_gov_reconciliation_status") == "reconciled"
    i_ok = intervention.get("intervention_execution_status") == "executed"
    if not r_ok:
        return {"fed_gov_ledger_status": "not_reconciled"}
    if not i_ok:
        return {"fed_gov_ledger_status": "no_intervention"}
    return {
        "fed_gov_ledger_status": "written",
        "fed_gov_ledger_entry_id": ledger_config.get("entry_id", "gle-0001"),
        "fed_gov_ledger_directive_id": intervention.get("executed_directive_id"),
    }
