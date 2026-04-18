from typing import Any

def validate_connector(connector: Any, egress_enforcement: Any, validator_config: Any) -> dict[str, Any]:
    if not isinstance(connector, dict) or not isinstance(egress_enforcement, dict):
        return {"connector_validation_status": "invalid"}
    c_ok = connector.get("connector_open_status") == "open"
    e_ok = egress_enforcement.get("egress_policy_enforcement_status") == "allowed"
    if not c_ok or not e_ok:
        return {"connector_validation_status": "invalid"}
    return {
        "connector_validation_status": "valid",
        "adapter_id": connector.get("adapter_id"),
    }
