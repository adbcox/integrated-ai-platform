from typing import Any


def attest_phase5_closure(
    checklist: dict[str, Any],
    certification_summary: dict[str, Any],
    attestation_config: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(checklist, dict)
        or not isinstance(certification_summary, dict)
        or not isinstance(attestation_config, dict)
    ):
        return {
            "closure_attestation_status": "invalid_input",
            "attestation_phase": None,
            "attestation_result": None,
        }

    checklist_ok = checklist.get("checklist_status") == "built"
    cert_ok = certification_summary.get("certification_summary_status") == "complete"

    if checklist_ok and cert_ok:
        return {
            "closure_attestation_status": "attested",
            "attestation_phase": checklist.get("checklist_phase"),
            "attestation_result": "closure_valid",
        }

    return {
        "closure_attestation_status": "failed",
        "attestation_phase": None,
        "attestation_result": None,
    }
