from typing import Any


def generate_phase4_terminal_report(
    gate_result: dict[str, Any],
    terminal_audit: dict[str, Any],
    seed_result: dict[str, Any],
    evidence_result: dict[str, Any],
    release_ledger: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(gate_result, dict)
        or not isinstance(terminal_audit, dict)
        or not isinstance(seed_result, dict)
        or not isinstance(evidence_result, dict)
        or not isinstance(release_ledger, dict)
    ):
        return {
            "report_valid": False,
            "transition_approved": False,
            "terminal_audit_passed": False,
            "seed_ready": False,
            "evidence_complete": False,
            "approved_release_count": 0,
            "phase4_complete": False,
            "completion_blockers": [],
            "terminal_status": "invalid_input",
        }

    transition_approved = gate_result.get("transition_approved", False) is True
    terminal_audit_passed = terminal_audit.get("terminal_audit_passed", False) is True
    seed_ready = seed_result.get("seed_ready", False) is True
    evidence_complete = evidence_result.get("evidence_complete", False) is True
    approved_release_count = int(release_ledger.get("approved_count", 0))

    blockers = []
    if not transition_approved:
        blockers.append("transition_approved")
    if not terminal_audit_passed:
        blockers.append("terminal_audit_passed")
    if not seed_ready:
        blockers.append("seed_ready")
    if not evidence_complete:
        blockers.append("evidence_complete")
    if approved_release_count <= 0:
        blockers.append("no_approved_releases")

    phase4_complete = len(blockers) == 0

    if phase4_complete:
        status = "complete"
    elif len(blockers) > 2:
        status = "blocked"
    else:
        status = "pending"

    return {
        "report_valid": True,
        "transition_approved": transition_approved,
        "terminal_audit_passed": terminal_audit_passed,
        "seed_ready": seed_ready,
        "evidence_complete": evidence_complete,
        "approved_release_count": approved_release_count,
        "phase4_complete": phase4_complete,
        "completion_blockers": blockers,
        "terminal_status": status,
    }


def summarize_phase4_terminal(result: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(result, dict) or result.get("report_valid") is not True:
        return {
            "summary_valid": False,
            "terminal_status": "invalid_input",
            "phase4_complete": False,
            "approved_release_count": 0,
        }

    return {
        "summary_valid": True,
        "terminal_status": result.get("terminal_status", "invalid_input"),
        "phase4_complete": bool(result.get("phase4_complete", False)),
        "approved_release_count": int(result.get("approved_release_count", 0)),
    }
