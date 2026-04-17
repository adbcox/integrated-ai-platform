from typing import Any


def summarize_phase5_capstone(
    cert_report: dict[str, Any],
    promo_report: dict[str, Any],
    handoff_report: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(cert_report, dict)
        or not isinstance(promo_report, dict)
        or not isinstance(handoff_report, dict)
    ):
        return {
            "capstone_summary_status": "failed",
            "capstone_phase": None,
            "capstone_completeness": 0,
        }

    cert_ok = cert_report.get("cert_report_status") == "complete"
    promo_ok = promo_report.get("promo_report_status") == "complete"
    handoff_ok = handoff_report.get("handoff_report_status") == "complete"

    if cert_ok and promo_ok and handoff_ok:
        return {
            "capstone_summary_status": "complete",
            "capstone_phase": cert_report.get("report_phase"),
            "capstone_completeness": 100,
        }

    return {
        "capstone_summary_status": "incomplete",
        "capstone_phase": None,
        "capstone_completeness": 0,
    }
