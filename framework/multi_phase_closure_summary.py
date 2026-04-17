from typing import Any


def summarize_closure(
    closure_attestation: dict[str, Any],
    certification_summary: dict[str, Any],
    promotion_summary: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(closure_attestation, dict)
        or not isinstance(certification_summary, dict)
        or not isinstance(promotion_summary, dict)
    ):
        return {
            "closure_summary_status": "invalid_input",
            "summary_phase": None,
            "summary_completeness": 0,
        }

    attest_ok = closure_attestation.get("closure_attestation_status") == "attested"
    cert_ok = certification_summary.get("certification_summary_status") == "complete"
    promo_ok = promotion_summary.get("promotion_summary_status") == "complete"

    if attest_ok and cert_ok and promo_ok:
        return {
            "closure_summary_status": "complete",
            "summary_phase": closure_attestation.get("attestation_phase"),
            "summary_completeness": 100,
        }

    return {
        "closure_summary_status": "incomplete",
        "summary_phase": None,
        "summary_completeness": 0,
    }
