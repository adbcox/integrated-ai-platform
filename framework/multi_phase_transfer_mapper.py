from typing import Any


def map_transfer(
    generalization: dict[str, Any],
    coordinator: dict[str, Any],
    target_config: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(generalization, dict)
        or not isinstance(coordinator, dict)
        or not isinstance(target_config, dict)
    ):
        return {
            "transfer_mapping_status": "invalid_input",
            "mapped_phase": None,
            "target_scope": None,
        }

    generalization_ok = generalization.get("generalization_status") == "generalized"
    coordinator_ok = coordinator.get("coordinator_status") == "initialized"

    if generalization_ok and coordinator_ok:
        return {
            "transfer_mapping_status": "mapped",
            "mapped_phase": coordinator.get("phase_id"),
            "target_scope": target_config.get("scope", "phase-5"),
        }

    if generalization_ok and not coordinator_ok:
        return {
            "transfer_mapping_status": "coordinator_not_ready",
            "mapped_phase": None,
            "target_scope": None,
        }

    if not generalization_ok:
        return {
            "transfer_mapping_status": "no_generalization",
            "mapped_phase": None,
            "target_scope": None,
        }

    return {
        "transfer_mapping_status": "invalid_input",
        "mapped_phase": None,
        "target_scope": None,
    }
