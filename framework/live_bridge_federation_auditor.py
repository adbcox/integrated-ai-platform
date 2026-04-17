from typing import Any

def audit_federation(fed_ledger_audit: dict[str, Any], fed_health: dict[str, Any], fed_anomaly: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(fed_ledger_audit, dict) or not isinstance(fed_health, dict) or not isinstance(fed_anomaly, dict):
        return {"fed_audit_status": "invalid_input"}
    l_ok = fed_ledger_audit.get("fed_ledger_audit_status") == "passed"
    h_ok = fed_health.get("fed_health_status") in ("green", "yellow")
    a_ok = fed_anomaly.get("fed_anomaly_status") == "none"
    return {"fed_audit_status": "passed"} if l_ok and h_ok and a_ok else {"fed_audit_status": "failed"}

