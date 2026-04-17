from typing import Any


def evaluate_phase_transition(
    terminal_audit: dict[str, Any],
    packet_result: dict[str, Any],
    controller_result: dict[str, Any],
    registry_audit: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(terminal_audit, dict)
        or not isinstance(packet_result, dict)
        or not isinstance(controller_result, dict)
        or not isinstance(registry_audit, dict)
    ):
        return {
            "gate_valid": False,
            "terminal_audit_passed": False,
            "packet_complete": False,
            "closure_complete": False,
            "registry_complete": False,
            "transition_approved": False,
            "gate_blockers": [],
            "gate_status": "invalid_input",
        }

    terminal_audit_passed = terminal_audit.get("terminal_audit_passed", False) is True
    packet_complete = packet_result.get("packet_complete", False) is True
    closure_complete = controller_result.get("controller_status") == "closed"
    registry_complete = registry_audit.get("registry_audit_status") == "complete"

    blockers = []
    if not terminal_audit_passed:
        blockers.append("terminal_audit_passed")
    if not packet_complete:
        blockers.append("packet_complete")
    if not closure_complete:
        blockers.append("closure_complete")
    if not registry_complete:
        blockers.append("registry_complete")

    transition_approved = len(blockers) == 0

    return {
        "gate_valid": True,
        "terminal_audit_passed": terminal_audit_passed,
        "packet_complete": packet_complete,
        "closure_complete": closure_complete,
        "registry_complete": registry_complete,
        "transition_approved": transition_approved,
        "gate_blockers": blockers,
        "gate_status": "open" if transition_approved else "blocked",
    }


def summarize_transition_gate(result: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(result, dict) or result.get("gate_valid") is not True:
        return {
            "summary_valid": False,
            "gate_status": "invalid_input",
            "transition_approved": False,
            "gate_blocker_count": 0,
        }

    return {
        "summary_valid": True,
        "gate_status": result.get("gate_status", "invalid_input"),
        "transition_approved": bool(result.get("transition_approved", False)),
        "gate_blocker_count": (
            len(result.get("gate_blockers", []))
            if isinstance(result.get("gate_blockers", []), list)
            else 0
        ),
    }
