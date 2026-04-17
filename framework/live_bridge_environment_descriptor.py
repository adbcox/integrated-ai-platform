from typing import Any


def describe_environment(
    env_config: dict[str, Any],
    target_descriptor: dict[str, Any],
    describer_config: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(env_config, dict)
        or not isinstance(target_descriptor, dict)
        or not isinstance(describer_config, dict)
    ):
        return {
            "env_descriptor_status": "invalid_input",
            "env_id": None,
            "env_kind": None,
            "env_scope": None,
        }

    if not isinstance(env_config, dict):
        return {
            "env_descriptor_status": "invalid_input",
            "env_id": None,
            "env_kind": None,
            "env_scope": None,
        }

    env_id = env_config.get("env_id")
    env_kind = env_config.get("env_kind")

    if not env_id or not env_kind:
        return {
            "env_descriptor_status": "invalid_env",
            "env_id": None,
            "env_kind": None,
            "env_scope": None,
        }

    return {
        "env_descriptor_status": "described",
        "env_id": env_id,
        "env_kind": env_kind,
        "env_scope": target_descriptor.get("scope", "default"),
    }
