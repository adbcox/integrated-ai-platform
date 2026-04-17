from typing import Any


def summarize_transfer(
    transfer_control_plane: dict[str, Any],
    transfer_auditor: dict[str, Any],
    mastery_assessor: dict[str, Any],
    summary_config: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(transfer_control_plane, dict)
        or not isinstance(transfer_auditor, dict)
        or not isinstance(mastery_assessor, dict)
        or not isinstance(summary_config, dict)
    ):
        return {
            "transfer_summary_status": "invalid_input",
            "summary_phase": None,
            "summary_level": None,
        }

    tcp_ok = transfer_control_plane.get("transfer_cp_status") == "operational"
    ta_ok = transfer_auditor.get("transfer_audit_status") == "passed"
    ma_ok = mastery_assessor.get("mastery_status") == "assessed"
    all_ok = tcp_ok and ta_ok and ma_ok

    if all_ok:
        return {
            "transfer_summary_status": "complete",
            "summary_phase": transfer_control_plane.get("cp_phase"),
            "summary_level": summary_config.get("level", "detailed"),
        }

    if (tcp_ok and ta_ok) or (tcp_ok and ma_ok) or (ta_ok and ma_ok):
        return {
            "transfer_summary_status": "partial",
            "summary_phase": None,
            "summary_level": None,
        }

    return {
        "transfer_summary_status": "incomplete",
        "summary_phase": None,
        "summary_level": None,
    }
