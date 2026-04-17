from typing import Any


def enforce_release_boundary(
    registry_audit: dict[str, Any],
    sign_off_aggregation: dict[str, Any],
    boundary_result: dict[str, Any],
    packet_result: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(registry_audit, dict)
        or not isinstance(sign_off_aggregation, dict)
        or not isinstance(boundary_result, dict)
        or not isinstance(packet_result, dict)
    ):
        return {
            "enforcement_valid": False,
            "registry_complete": False,
            "sign_off_passed": False,
            "boundary_clean": False,
            "packet_complete": False,
            "release_approved": False,
            "blocking_items": [],
            "enforcement_status": "invalid_input",
        }

    registry_complete = registry_audit.get("registry_audit_status") == "complete"
    sign_off_passed = sign_off_aggregation.get("aggregation_status") == "gate_passed"
    boundary_clean = boundary_result.get("boundary_status") == "clean"
    packet_complete = packet_result.get("packet_status") == "complete"

    blocking = []
    if not registry_complete:
        blocking.append("registry_complete")
    if not sign_off_passed:
        blocking.append("sign_off_passed")
    if not boundary_clean:
        blocking.append("boundary_clean")
    if not packet_complete:
        blocking.append("packet_complete")

    release_approved = len(blocking) == 0

    return {
        "enforcement_valid": True,
        "registry_complete": registry_complete,
        "sign_off_passed": sign_off_passed,
        "boundary_clean": boundary_clean,
        "packet_complete": packet_complete,
        "release_approved": release_approved,
        "blocking_items": blocking,
        "enforcement_status": "approved" if release_approved else "blocked",
    }


def summarize_release_enforcement(result: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(result, dict) or result.get("enforcement_valid") is not True:
        return {
            "summary_valid": False,
            "enforcement_status": "invalid_input",
            "release_approved": False,
            "blocking_item_count": 0,
        }

    return {
        "summary_valid": True,
        "enforcement_status": result.get("enforcement_status", "invalid_input"),
        "release_approved": bool(result.get("release_approved", False)),
        "blocking_item_count": (
            len(result.get("blocking_items", []))
            if isinstance(result.get("blocking_items", []), list)
            else 0
        ),
    }
