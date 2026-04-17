from typing import Any


def seed_next_phase(
    gate_result: dict[str, Any],
    release_ledger: dict[str, Any],
    terminal_audit: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(gate_result, dict)
        or not isinstance(release_ledger, dict)
        or not isinstance(terminal_audit, dict)
    ):
        return {
            "seed_valid": False,
            "source_phase": "phase-4",
            "target_phase": "phase-5",
            "transition_approved": False,
            "approved_release_count": 0,
            "terminal_audit_passed": False,
            "seed_ready": False,
            "seed_payload": {},
            "seed_status": "invalid_input",
        }

    transition_approved = gate_result.get("transition_approved", False) is True
    approved_release_count = int(release_ledger.get("approved_count", 0))
    terminal_audit_passed = terminal_audit.get("terminal_audit_passed", False) is True

    seed_ready = transition_approved and terminal_audit_passed
    payload = {
        "from_phase": "phase-4",
        "approved_releases": approved_release_count,
        "terminal_status": terminal_audit.get("terminal_audit_status", "unknown"),
    }

    return {
        "seed_valid": True,
        "source_phase": "phase-4",
        "target_phase": "phase-5",
        "transition_approved": transition_approved,
        "approved_release_count": approved_release_count,
        "terminal_audit_passed": terminal_audit_passed,
        "seed_ready": seed_ready,
        "seed_payload": payload,
        "seed_status": "seeded" if seed_ready else "blocked",
    }


def summarize_seed(result: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(result, dict) or result.get("seed_valid") is not True:
        return {
            "summary_valid": False,
            "seed_status": "invalid_input",
            "seed_ready": False,
            "target_phase": "phase-5",
        }

    return {
        "summary_valid": True,
        "seed_status": result.get("seed_status", "invalid_input"),
        "seed_ready": bool(result.get("seed_ready", False)),
        "target_phase": result.get("target_phase", "phase-5"),
    }
