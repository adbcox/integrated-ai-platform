from typing import Any


def report_phase5_certification(
    cert_finalization: dict[str, Any],
    certification_summary: dict[str, Any],
    phase_id: str,
) -> dict[str, Any]:
    if (
        not isinstance(cert_finalization, dict)
        or not isinstance(certification_summary, dict)
        or not isinstance(phase_id, str)
    ):
        return {
            "cert_report_status": "failed",
            "report_phase": None,
            "report_sections": 0,
        }

    final_ok = cert_finalization.get("cert_finalization_status") == "finalized"
    sum_ok = certification_summary.get("certification_summary_status") == "complete"

    if final_ok and sum_ok:
        return {
            "cert_report_status": "complete",
            "report_phase": cert_finalization.get("finalization_phase"),
            "report_sections": certification_summary.get("summary_sections", 0),
        }

    return {
        "cert_report_status": "incomplete",
        "report_phase": None,
        "report_sections": 0,
    }
