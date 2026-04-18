from typing import Any

def audit_obs_layer(obs_ledger_audit: Any) -> dict[str, Any]:
    if not isinstance(obs_ledger_audit, dict):
        return {"obs_layer_audit_status": "not_audited"}
    ledger_ok = obs_ledger_audit.get("obs_ledger_audit_status") == "passed"
    if not ledger_ok:
        return {"obs_layer_audit_status": "not_audited"}
    return {
        "obs_layer_audit_status": "passed",
    }
