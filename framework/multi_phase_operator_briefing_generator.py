from typing import Any


def generate_operator_briefing(
    manifest: dict[str, Any],
    phase5_summary: dict[str, Any],
    briefing_config: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(manifest, dict)
        or not isinstance(phase5_summary, dict)
        or not isinstance(briefing_config, dict)
    ):
        return {
            "briefing_status": "invalid_input",
            "briefing_phase": None,
            "briefing_sections": 0,
        }

    manifest_ok = manifest.get("manifest_status") == "built"
    summary_ok = phase5_summary.get("summary_status") == "complete"

    if manifest_ok and summary_ok:
        return {
            "briefing_status": "generated",
            "briefing_phase": manifest.get("manifest_phase"),
            "briefing_sections": 5,
        }

    return {
        "briefing_status": "failed",
        "briefing_phase": None,
        "briefing_sections": 0,
    }
