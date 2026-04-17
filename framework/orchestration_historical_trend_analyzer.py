from typing import Any


def analyze_historical_trends(
    phase_reports: list[dict[str, Any]],
) -> dict[str, Any]:
    if not isinstance(phase_reports, list):
        return {
            "analysis_valid": False,
            "phase_count": 0,
            "sign_off_count": 0,
            "sign_off_rate": 0.0,
            "success_count": 0,
            "success_rate": 0.0,
            "trend_direction": "unknown",
            "trend_status": "invalid_input",
        }

    if len(phase_reports) == 0:
        return {
            "analysis_valid": True,
            "phase_count": 0,
            "sign_off_count": 0,
            "sign_off_rate": 0.0,
            "success_count": 0,
            "success_rate": 0.0,
            "trend_direction": "stable",
            "trend_status": "empty_history",
        }

    phase_count = len(phase_reports)
    sign_off_count = 0
    success_count = 0

    for report in phase_reports:
        if isinstance(report, dict):
            if report.get("phase_sign_off") is True:
                sign_off_count += 1
            if report.get("final_report_status") == "signed_off":
                success_count += 1

    sign_off_rate = round((sign_off_count / float(phase_count)) * 100.0, 1) if phase_count > 0 else 0.0
    success_rate = round((success_count / float(phase_count)) * 100.0, 1) if phase_count > 0 else 0.0

    if len(phase_reports) >= 2:
        recent_success = 1 if phase_reports[-1].get("final_report_status") == "signed_off" else 0
        prior_success = 1 if phase_reports[-2].get("final_report_status") == "signed_off" else 0
        if recent_success > prior_success:
            trend_direction = "improving"
        elif recent_success < prior_success:
            trend_direction = "declining"
        else:
            trend_direction = "stable"
    else:
        trend_direction = "stable"

    return {
        "analysis_valid": True,
        "phase_count": phase_count,
        "sign_off_count": sign_off_count,
        "sign_off_rate": sign_off_rate,
        "success_count": success_count,
        "success_rate": success_rate,
        "trend_direction": trend_direction,
        "trend_status": "complete",
    }


def summarize_historical_trends(result: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(result, dict) or result.get("analysis_valid") is not True:
        return {
            "summary_valid": False,
            "trend_status": "invalid_input",
            "trend_direction": "unknown",
            "success_rate": 0.0,
        }

    return {
        "summary_valid": True,
        "trend_status": result.get("trend_status", "invalid_input"),
        "trend_direction": result.get("trend_direction", "unknown"),
        "success_rate": float(result.get("success_rate", 0.0)),
    }
