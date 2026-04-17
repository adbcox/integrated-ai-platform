from typing import Any


def summarize_self_evaluation(
    self_evaluation_control_plane: dict[str, Any],
    critique_auditor: dict[str, Any],
    critique_rollup: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(self_evaluation_control_plane, dict)
        or not isinstance(critique_auditor, dict)
        or not isinstance(critique_rollup, dict)
    ):
        return {
            "self_eval_summary_status": "invalid_input",
            "summary_phase": None,
            "summary_level": None,
        }

    secp_ok = self_evaluation_control_plane.get("self_eval_cp_status") == "operational"
    ca_ok = critique_auditor.get("critique_audit_status") == "passed"
    cr_ok = critique_rollup.get("critique_rollup_status") == "rolled_up"
    all_ok = secp_ok and ca_ok and cr_ok

    if all_ok:
        return {
            "self_eval_summary_status": "complete",
            "summary_phase": self_evaluation_control_plane.get("cp_phase"),
            "summary_level": "detailed",
        }

    if (secp_ok and ca_ok) or (secp_ok and cr_ok) or (ca_ok and cr_ok):
        return {
            "self_eval_summary_status": "partial",
            "summary_phase": None,
            "summary_level": None,
        }

    return {
        "self_eval_summary_status": "incomplete",
        "summary_phase": None,
        "summary_level": None,
    }
