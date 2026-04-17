from typing import Any

def audit_fed_gov_ledger(ledger: dict, reconciliation: dict, auditor_config: dict) -> dict:
    if not isinstance(ledger, dict) or not isinstance(reconciliation, dict) or not isinstance(auditor_config, dict):
        return {"fed_gov_ledger_audit_status": "invalid_input"}
    l_ok = ledger.get("fed_gov_ledger_status") == "written"
    r_ok = reconciliation.get("fed_gov_reconciliation_status") == "reconciled"
    all_ok = l_ok and r_ok
    any_ok = l_ok or r_ok
    if all_ok:
        return {
            "fed_gov_ledger_audit_status": "passed",
            "fed_gov_audit_entry_id": ledger.get("fed_gov_ledger_entry_id"),
            "fed_gov_audit_ok_count": 2,
        }
    if any_ok:
        return {
            "fed_gov_ledger_audit_status": "degraded",
            "fed_gov_audit_ok_count": int(l_ok) + int(r_ok),
        }
    return {"fed_gov_ledger_audit_status": "failed", "fed_gov_audit_ok_count": 0}
