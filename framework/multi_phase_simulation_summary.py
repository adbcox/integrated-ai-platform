from typing import Any


def summarize_simulation(
    self_evaluation_control_plane: dict[str, Any],
    robustness_scorer: dict[str, Any],
    adversarial_tester: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(self_evaluation_control_plane, dict)
        or not isinstance(robustness_scorer, dict)
        or not isinstance(adversarial_tester, dict)
    ):
        return {
            "simulation_summary_status": "invalid_input",
            "summary_phase": None,
            "summary_level": None,
        }

    secp_ok = self_evaluation_control_plane.get("self_eval_cp_status") == "operational"
    rs_ok = robustness_scorer.get("robustness_status") == "scored"
    at_ok = adversarial_tester.get("adversarial_status") == "tested"
    all_ok = secp_ok and rs_ok and at_ok

    if all_ok:
        return {
            "simulation_summary_status": "complete",
            "summary_phase": self_evaluation_control_plane.get("cp_phase"),
            "summary_level": "detailed",
        }

    if (secp_ok and rs_ok) or (secp_ok and at_ok) or (rs_ok and at_ok):
        return {
            "simulation_summary_status": "partial",
            "summary_phase": None,
            "summary_level": None,
        }

    return {
        "simulation_summary_status": "incomplete",
        "summary_phase": None,
        "summary_level": None,
    }
