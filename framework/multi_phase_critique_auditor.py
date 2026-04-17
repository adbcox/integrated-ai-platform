from typing import Any


def audit_critique(
    critique_extraction: dict[str, Any],
    counterfactual_critique: dict[str, Any],
    weakness_detector: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(critique_extraction, dict)
        or not isinstance(counterfactual_critique, dict)
        or not isinstance(weakness_detector, dict)
    ):
        return {
            "critique_audit_status": "invalid_input",
            "audit_phase": None,
            "audit_result": None,
        }

    ce_ok = critique_extraction.get("critique_status") == "extracted"
    cc_ok = counterfactual_critique.get("cf_critique_status") == "synthesized"
    wd_ok = weakness_detector.get("weakness_status") == "detected"
    all_ok = ce_ok and cc_ok and wd_ok

    if all_ok:
        return {
            "critique_audit_status": "passed",
            "audit_phase": critique_extraction.get("critique_phase"),
            "audit_result": "critique_valid",
        }

    if (ce_ok and cc_ok) or (ce_ok and wd_ok):
        return {
            "critique_audit_status": "degraded",
            "audit_phase": None,
            "audit_result": None,
        }

    return {
        "critique_audit_status": "failed",
        "audit_phase": None,
        "audit_result": None,
    }
