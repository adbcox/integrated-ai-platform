from typing import Any


def register_environment(
    descriptor: dict[str, Any],
    capstone_closure: dict[str, Any],
    registrar_config: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(descriptor, dict)
        or not isinstance(capstone_closure, dict)
        or not isinstance(registrar_config, dict)
    ):
        return {
            "env_registration_status": "invalid_input",
            "registered_env_id": None,
            "registrar_id": None,
        }

    desc_ok = descriptor.get("env_descriptor_status") == "described"
    closure_ok = capstone_closure.get("capstone_closure_report_status") == "complete"

    if not desc_ok:
        return {
            "env_registration_status": "no_descriptor",
            "registered_env_id": None,
            "registrar_id": None,
        }

    if desc_ok and not closure_ok:
        return {
            "env_registration_status": "capstone_not_closed",
            "registered_env_id": None,
            "registrar_id": None,
        }

    if desc_ok and closure_ok:
        return {
            "env_registration_status": "registered",
            "registered_env_id": descriptor.get("env_id"),
            "registrar_id": registrar_config.get("registrar_id", "reg-0001"),
        }

    return {
        "env_registration_status": "failed",
        "registered_env_id": None,
        "registrar_id": None,
    }
