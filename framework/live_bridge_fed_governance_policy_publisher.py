from typing import Any

def publish_fed_policy(validation: dict, fed_cp: dict, publisher_config: dict) -> dict:
    if not isinstance(validation, dict) or not isinstance(fed_cp, dict) or not isinstance(publisher_config, dict):
        return {"fed_policy_publication_status": "invalid_input"}
    v_ok = validation.get("fed_policy_validation_status") == "valid"
    cp_op = fed_cp.get("fed_cp_status") == "operational"
    if not v_ok:
        return {"fed_policy_publication_status": "not_valid"}
    if not cp_op:
        return {"fed_policy_publication_status": "fed_offline"}
    return {
        "fed_policy_publication_status": "published",
        "published_fed_policy_id": validation.get("validated_fed_policy_id"),
        "published_env_id": fed_cp.get("fed_cp_env_id"),
    }
