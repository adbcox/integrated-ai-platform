from typing import Any


def gate_certification(
    certification_summary: dict[str, Any],
    publication: dict[str, Any],
    closure_attestation: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(certification_summary, dict)
        or not isinstance(publication, dict)
        or not isinstance(closure_attestation, dict)
    ):
        return {
            "cert_gate_status": "blocked",
            "gate_phase": None,
            "gate_result": None,
        }

    cert_ok = certification_summary.get("certification_summary_status") == "complete"
    pub_ok = publication.get("publication_status") == "published"
    attest_ok = closure_attestation.get("closure_attestation_status") == "attested"

    if cert_ok and pub_ok and attest_ok:
        return {
            "cert_gate_status": "open",
            "gate_phase": certification_summary.get("summary_phase"),
            "gate_result": "cert_ready",
        }

    return {
        "cert_gate_status": "blocked",
        "gate_phase": None,
        "gate_result": None,
    }
