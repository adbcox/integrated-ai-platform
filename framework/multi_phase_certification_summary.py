from typing import Any


def summarize_certification(
    cert_cp: dict[str, Any],
    publication: dict[str, Any],
    ledger_audit: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(cert_cp, dict)
        or not isinstance(publication, dict)
        or not isinstance(ledger_audit, dict)
    ):
        return {
            "certification_summary_status": "invalid_input",
            "summary_phase": None,
            "summary_sections": 0,
        }

    cp_ok = cert_cp.get("cert_cp_status") == "operational"
    pub_ok = publication.get("publication_status") == "published"
    audit_ok = ledger_audit.get("ledger_audit_status") == "passed"

    if cp_ok and pub_ok and audit_ok:
        return {
            "certification_summary_status": "complete",
            "summary_phase": cert_cp.get("cp_phase"),
            "summary_sections": 5,
        }

    return {
        "certification_summary_status": "incomplete",
        "summary_phase": None,
        "summary_sections": 0,
    }
