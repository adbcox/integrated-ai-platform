from typing import Any

def build_fed_governance_control_plane(fed_gov_validation: dict, fed_gov_rollup: dict, event_bus: dict) -> dict:
    if not isinstance(fed_gov_validation, dict) or not isinstance(fed_gov_rollup, dict) or not isinstance(event_bus, dict):
        return {"fed_gov_cp_status": "invalid_input"}
    fv_ok = fed_gov_validation.get("fed_gov_validation_status") == "valid"
    fr_ok = fed_gov_rollup.get("fed_gov_rollup_status") == "rolled_up"
    all_complete = fv_ok and fr_ok
    msg_count = event_bus.get("message_count", -1)
    if all_complete and msg_count >= 0:
        return {
            "fed_gov_cp_status": "operational",
            "fed_gov_cp_env_id": fed_gov_validation.get("validated_fed_gov_env_id"),
            "component_count": 3,
        }
    if fv_ok != fr_ok:
        return {"fed_gov_cp_status": "degraded"}
    return {"fed_gov_cp_status": "offline"}
