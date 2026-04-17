from typing import Any


def summarize_generalization(
    generalization_control_plane: dict[str, Any],
    generalization_reporter: dict[str, Any],
    summary_config: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(generalization_control_plane, dict)
        or not isinstance(generalization_reporter, dict)
        or not isinstance(summary_config, dict)
    ):
        return {
            "generalization_summary_status": "invalid_input",
            "summary_phase": None,
            "summary_level": None,
        }

    gcp_ok = generalization_control_plane.get("generalization_cp_status") == "operational"
    gr_ok = generalization_reporter.get("generalization_report_status") == "complete"
    all_ok = gcp_ok and gr_ok

    if all_ok:
        return {
            "generalization_summary_status": "complete",
            "summary_phase": generalization_control_plane.get("cp_phase"),
            "summary_level": summary_config.get("level", "detailed"),
        }

    if gcp_ok or gr_ok:
        return {
            "generalization_summary_status": "partial",
            "summary_phase": None,
            "summary_level": None,
        }

    return {
        "generalization_summary_status": "incomplete",
        "summary_phase": None,
        "summary_level": None,
    }
