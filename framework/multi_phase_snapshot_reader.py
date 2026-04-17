from typing import Any


def read_phase_snapshot(
    snapshot: dict[str, Any],
    requesting_phase: str,
) -> dict[str, Any]:
    if (
        not isinstance(snapshot, dict)
        or not isinstance(requesting_phase, str)
        or not requesting_phase
    ):
        return {
            "read_status": "invalid_input",
            "read_phase": None,
            "resource_count": 0,
        }

    snapshot_status = snapshot.get("snapshot_status")
    snapshot_phase = snapshot.get("snapshot_phase")

    if snapshot_status != "written":
        return {
            "read_status": "snapshot_not_written",
            "read_phase": None,
            "resource_count": 0,
        }

    if snapshot_phase != requesting_phase:
        return {
            "read_status": "phase_mismatch",
            "read_phase": None,
            "resource_count": 0,
        }

    return {
        "read_status": "read",
        "read_phase": requesting_phase,
        "resource_count": snapshot.get("resource_count", 0),
    }
