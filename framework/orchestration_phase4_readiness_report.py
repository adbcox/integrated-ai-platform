from typing import Any


def generate_phase4_readiness_report(
    consolidation_result: dict[str, Any],
    enforcement_result: dict[str, Any],
    trend_result: dict[str, Any],
    controller_result: dict[str, Any],
    registry_audit: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(consolidation_result, dict)
        or not isinstance(enforcement_result, dict)
        or not isinstance(trend_result, dict)
        or not isinstance(controller_result, dict)
        or not isinstance(registry_audit, dict)
    ):
        return {
            "report_valid": False,
            "sign_off_consolidated": False,
            "release_approved": False,
            "replay_reliable": False,
            "closure_complete": False,
            "registry_complete": False,
            "phase4_ready": False,
            "blocking_conditions": [],
            "phase4_status": "invalid_input",
        }

    sign_off_consolidated = consolidation_result.get("consolidated_sign_off", False) is True
    release_approved = enforcement_result.get("release_approved", False) is True
    replay_reliable = trend_result.get("replay_trend") in ("reliable", "insufficient_data")
    closure_complete = controller_result.get("controller_status") == "closed"
    registry_complete = registry_audit.get("registry_audit_status") == "complete"

    blocking = []
    if not sign_off_consolidated:
        blocking.append("sign_off_consolidated")
    if not release_approved:
        blocking.append("release_approved")
    if not replay_reliable:
        blocking.append("replay_reliable")
    if not closure_complete:
        blocking.append("closure_complete")
    if not registry_complete:
        blocking.append("registry_complete")

    phase4_ready = len(blocking) == 0

    if phase4_ready:
        status = "ready"
    elif len(blocking) > 2:
        status = "blocked"
    else:
        status = "pending"

    return {
        "report_valid": True,
        "sign_off_consolidated": sign_off_consolidated,
        "release_approved": release_approved,
        "replay_reliable": replay_reliable,
        "closure_complete": closure_complete,
        "registry_complete": registry_complete,
        "phase4_ready": phase4_ready,
        "blocking_conditions": blocking,
        "phase4_status": status,
    }


def summarize_phase4_readiness(result: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(result, dict) or result.get("report_valid") is not True:
        return {
            "summary_valid": False,
            "phase4_status": "invalid_input",
            "phase4_ready": False,
            "blocking_condition_count": 0,
        }

    return {
        "summary_valid": True,
        "phase4_status": result.get("phase4_status", "invalid_input"),
        "phase4_ready": bool(result.get("phase4_ready", False)),
        "blocking_condition_count": (
            len(result.get("blocking_conditions", []))
            if isinstance(result.get("blocking_conditions", []), list)
            else 0
        ),
    }
