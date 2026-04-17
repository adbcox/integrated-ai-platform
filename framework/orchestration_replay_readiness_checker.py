from typing import Any


def check_replay_readiness(
    archive_result: dict[str, Any],
    checkpoint_result: dict[str, Any],
    trail_result: dict[str, Any],
    integrity_result: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(archive_result, dict)
        or not isinstance(checkpoint_result, dict)
        or not isinstance(trail_result, dict)
        or not isinstance(integrity_result, dict)
    ):
        return {
            "readiness_valid": False,
            "archive_present": False,
            "checkpoint_present": False,
            "trail_present": False,
            "integrity_intact": False,
            "replay_ready": False,
            "missing_prerequisites": [],
            "readiness_status": "invalid_input",
        }

    archive_present = archive_result.get("archive_status") == "archived"
    checkpoint_present = checkpoint_result.get("checkpoint_status") == "written"
    trail_present = trail_result.get("trail_status") in ("complete", "partial")
    integrity_intact = integrity_result.get("integrity_status") == "intact"

    missing = []
    if not archive_present:
        missing.append("archive_present")
    if not checkpoint_present:
        missing.append("checkpoint_present")
    if not trail_present:
        missing.append("trail_present")
    if not integrity_intact:
        missing.append("integrity_intact")

    replay_ready = len(missing) == 0

    return {
        "readiness_valid": True,
        "archive_present": archive_present,
        "checkpoint_present": checkpoint_present,
        "trail_present": trail_present,
        "integrity_intact": integrity_intact,
        "replay_ready": replay_ready,
        "missing_prerequisites": missing,
        "readiness_status": "ready" if replay_ready else "not_ready",
    }


def summarize_replay_readiness(result: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(result, dict) or result.get("readiness_valid") is not True:
        return {
            "summary_valid": False,
            "readiness_status": "invalid_input",
            "replay_ready": False,
            "missing_count": 0,
        }

    return {
        "summary_valid": True,
        "readiness_status": result.get("readiness_status", "invalid_input"),
        "replay_ready": bool(result.get("replay_ready", False)),
        "missing_count": (
            len(result.get("missing_prerequisites", []))
            if isinstance(result.get("missing_prerequisites", []), list)
            else 0
        ),
    }
