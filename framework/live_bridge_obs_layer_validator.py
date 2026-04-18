from typing import Any

def validate_obs_layer(obs_layer_audit: Any) -> dict[str, Any]:
    if not isinstance(obs_layer_audit, dict):
        return {"obs_layer_validation_status": "not_validated"}
    audit_ok = obs_layer_audit.get("obs_layer_audit_status") == "passed"
    if not audit_ok:
        return {"obs_layer_validation_status": "not_validated"}
    return {
        "obs_layer_validation_status": "valid",
    }
