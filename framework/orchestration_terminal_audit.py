from typing import Any


def run_terminal_audit(
    evidence_result: dict[str, Any],
    release_ledger: dict[str, Any],
    consolidation_result: dict[str, Any],
    phase4_readiness: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(evidence_result, dict)
        or not isinstance(release_ledger, dict)
        or not isinstance(consolidation_result, dict)
        or not isinstance(phase4_readiness, dict)
    ):
        return {
            "audit_valid": False,
            "evidence_complete": False,
            "releases_approved": False,
            "sign_off_consolidated": False,
            "phase4_ready": False,
            "terminal_audit_passed": False,
            "failed_checks": [],
            "terminal_audit_status": "invalid_input",
        }

    evidence_complete = evidence_result.get("evidence_complete", False) is True
    approved_count = int(release_ledger.get("approved_count", 0))
    release_count = int(release_ledger.get("release_count", -1))
    releases_approved = approved_count > 0 and approved_count == release_count
    sign_off_consolidated = consolidation_result.get("consolidated_sign_off", False) is True
    phase4_ready = phase4_readiness.get("phase4_ready", False) is True

    failed = []
    if not evidence_complete:
        failed.append("evidence_complete")
    if not releases_approved:
        failed.append("releases_approved")
    if not sign_off_consolidated:
        failed.append("sign_off_consolidated")
    if not phase4_ready:
        failed.append("phase4_ready")

    terminal_audit_passed = len(failed) == 0

    if terminal_audit_passed:
        status = "passed"
    elif len(failed) == 4:
        status = "failed"
    else:
        status = "partial"

    return {
        "audit_valid": True,
        "evidence_complete": evidence_complete,
        "releases_approved": releases_approved,
        "sign_off_consolidated": sign_off_consolidated,
        "phase4_ready": phase4_ready,
        "terminal_audit_passed": terminal_audit_passed,
        "failed_checks": failed,
        "terminal_audit_status": status,
    }


def summarize_terminal_audit(result: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(result, dict) or result.get("audit_valid") is not True:
        return {
            "summary_valid": False,
            "terminal_audit_status": "invalid_input",
            "terminal_audit_passed": False,
            "failed_check_count": 0,
        }

    return {
        "summary_valid": True,
        "terminal_audit_status": result.get("terminal_audit_status", "invalid_input"),
        "terminal_audit_passed": bool(result.get("terminal_audit_passed", False)),
        "failed_check_count": (
            len(result.get("failed_checks", []))
            if isinstance(result.get("failed_checks", []), list)
            else 0
        ),
    }
