from typing import Any

def audit_obs_ledger(obs_ledger_write: Any) -> dict[str, Any]:
    if not isinstance(obs_ledger_write, dict):
        return {"obs_ledger_audit_status": "not_audited"}
    write_ok = obs_ledger_write.get("obs_ledger_write_status") == "written"
    if not write_ok:
        return {"obs_ledger_audit_status": "not_audited"}
    return {
        "obs_ledger_audit_status": "passed",
    }
