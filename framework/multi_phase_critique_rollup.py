from typing import Any


def rollup_critique(
    critique_extraction: dict[str, Any],
    counterfactual_critique: dict[str, Any],
    critique_reporter: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(critique_extraction, dict)
        or not isinstance(counterfactual_critique, dict)
        or not isinstance(critique_reporter, dict)
    ):
        return {
            "critique_rollup_status": "invalid_input",
            "rollup_phase": None,
            "rollup_count": 0,
        }

    ce_ok = critique_extraction.get("critique_status") == "extracted"
    cc_ok = counterfactual_critique.get("cf_critique_status") == "synthesized"
    cr_ok = critique_reporter.get("critique_report_status") == "complete"
    all_ok = ce_ok and cc_ok and cr_ok

    if all_ok:
        return {
            "critique_rollup_status": "rolled_up",
            "rollup_phase": critique_extraction.get("critique_phase"),
            "rollup_count": critique_extraction.get("critique_count", 0),
        }

    if (ce_ok and cc_ok) or (ce_ok and cr_ok):
        return {
            "critique_rollup_status": "degraded",
            "rollup_phase": None,
            "rollup_count": 0,
        }

    return {
        "critique_rollup_status": "offline",
        "rollup_phase": None,
        "rollup_count": 0,
    }
