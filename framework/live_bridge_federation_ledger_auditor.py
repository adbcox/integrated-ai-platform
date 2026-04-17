from typing import Any

def audit_federation_ledger(fed_ledger: dict[str, Any], merge: dict[str, Any], auditor_config: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(fed_ledger, dict) or not isinstance(merge, dict) or not isinstance(auditor_config, dict):
        return {"fed_ledger_audit_status": "invalid_input"}
    l_ok = fed_ledger.get("fed_ledger_status") == "written"
    m_ok = merge.get("merge_status") == "merged"
    return {"fed_ledger_audit_status": "passed"} if l_ok and m_ok else {"fed_ledger_audit_status": "failed"}

