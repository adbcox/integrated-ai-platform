from typing import Any


def assemble_sign_off_packet(
    phase4_readiness: dict[str, Any],
    consolidation_result: dict[str, Any],
    enforcement_result: dict[str, Any],
    handoff_rollup: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(phase4_readiness, dict)
        or not isinstance(consolidation_result, dict)
        or not isinstance(enforcement_result, dict)
        or not isinstance(handoff_rollup, dict)
    ):
        return {
            "packet_valid": False,
            "phase4_ready": False,
            "consolidated_sign_off": False,
            "release_approved": False,
            "all_handoffs_approved": False,
            "packet_complete": False,
            "missing_signals": [],
            "packet_status": "invalid_input",
        }

    phase4_ready = phase4_readiness.get("phase4_ready", False) is True
    consolidated_sign_off = consolidation_result.get("consolidated_sign_off", False) is True
    release_approved = enforcement_result.get("release_approved", False) is True
    all_handoffs_approved = handoff_rollup.get("all_approved", False) is True

    missing = []
    if not phase4_ready:
        missing.append("phase4_ready")
    if not consolidated_sign_off:
        missing.append("consolidated_sign_off")
    if not release_approved:
        missing.append("release_approved")
    if not all_handoffs_approved:
        missing.append("all_handoffs_approved")

    packet_complete = len(missing) == 0

    return {
        "packet_valid": True,
        "phase4_ready": phase4_ready,
        "consolidated_sign_off": consolidated_sign_off,
        "release_approved": release_approved,
        "all_handoffs_approved": all_handoffs_approved,
        "packet_complete": packet_complete,
        "missing_signals": missing,
        "packet_status": "complete" if packet_complete else "partial",
    }


def summarize_sign_off_packet(result: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(result, dict) or result.get("packet_valid") is not True:
        return {
            "summary_valid": False,
            "packet_status": "invalid_input",
            "packet_complete": False,
            "missing_signal_count": 0,
        }

    return {
        "summary_valid": True,
        "packet_status": result.get("packet_status", "invalid_input"),
        "packet_complete": bool(result.get("packet_complete", False)),
        "missing_signal_count": (
            len(result.get("missing_signals", []))
            if isinstance(result.get("missing_signals", []), list)
            else 0
        ),
    }
