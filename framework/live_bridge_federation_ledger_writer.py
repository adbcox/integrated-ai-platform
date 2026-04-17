from typing import Any

def write_federation_ledger(merge: dict[str, Any], ownership: dict[str, Any], ledger_config: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(merge, dict) or not isinstance(ownership, dict) or not isinstance(ledger_config, dict):
        return {"fed_ledger_status": "invalid_input", "ledger_id": None}
    m_ok = merge.get("merge_status") == "merged"
    o_ok = ownership.get("ownership_status") == "arbitrated"
    return {"fed_ledger_status": "written", "ledger_id": ledger_config.get("ledger_id", "fledg-0001")} if m_ok and o_ok else {"fed_ledger_status": "prerequisites_failed", "ledger_id": None}

