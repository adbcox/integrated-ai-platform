from typing import Any


def validate_environment(
    registration: dict[str, Any],
    governance_cp: dict[str, Any],
    validator_config: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(registration, dict)
        or not isinstance(governance_cp, dict)
        or not isinstance(validator_config, dict)
    ):
        return {
            "env_validation_status": "invalid_input",
            "validated_env_id": None,
            "validation_scope": None,
        }

    r_ok = registration.get("env_registration_status") == "registered"
    g_op = governance_cp.get("governance_cp_status") == "operational"

    if not r_ok:
        return {
            "env_validation_status": "not_registered",
            "validated_env_id": None,
            "validation_scope": None,
        }

    if r_ok and not g_op:
        return {
            "env_validation_status": "governance_offline",
            "validated_env_id": None,
            "validation_scope": None,
        }

    return {
        "env_validation_status": "valid",
        "validated_env_id": registration.get("registered_env_id"),
        "validation_scope": validator_config.get("scope", "standard"),
    }
