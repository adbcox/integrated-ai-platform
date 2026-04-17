from typing import Any

def watch_supervisory_health(quorum_validation: dict, fed_health: dict, watch_config: dict) -> dict:
    if not isinstance(quorum_validation, dict) or not isinstance(fed_health, dict) or not isinstance(watch_config, dict):
        return {"supervisory_health_status": "invalid_input"}
    q_valid = quorum_validation.get("quorum_validation_status") == "valid"
    fh_status = fed_health.get("fed_health_status")
    fh_green = fh_status == "green"
    fh_yellow = fh_status == "yellow"
    fh_red = fh_status == "red"
    if q_valid and fh_green:
        return {
            "supervisory_health_status": "green",
            "supervisory_health_env_id": quorum_validation.get("validated_quorum_id"),
            "supervisory_quorum_size": quorum_validation.get("validated_quorum_size", 0),
        }
    if q_valid and fh_yellow:
        return {"supervisory_health_status": "yellow"}
    return {"supervisory_health_status": "red"}
