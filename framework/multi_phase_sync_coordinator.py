from typing import Any


def coordinate_phase_sync(
    divergence: dict[str, Any],
    control_plane: dict[str, Any],
    sync_policy: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(divergence, dict)
        or not isinstance(control_plane, dict)
        or not isinstance(sync_policy, dict)
    ):
        return {
            "sync_status": "invalid_input",
            "sync_phase": None,
            "policy_applied": None,
        }

    divergence_status = divergence.get("divergence_status")
    control_plane_status = control_plane.get("control_plane_status")

    cp_operational = control_plane_status == "operational"

    if not cp_operational:
        return {
            "sync_status": "control_plane_not_operational",
            "sync_phase": None,
            "policy_applied": None,
        }

    if divergence_status == "no_divergence":
        return {
            "sync_status": "synced",
            "sync_phase": control_plane.get("active_phase"),
            "policy_applied": sync_policy.get("strategy", "default"),
        }

    if divergence_status == "diverged":
        return {
            "sync_status": "sync_required",
            "sync_phase": control_plane.get("active_phase"),
            "policy_applied": None,
        }

    return {
        "sync_status": "invalid_input",
        "sync_phase": None,
        "policy_applied": None,
    }
