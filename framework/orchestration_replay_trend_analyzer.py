from typing import Any


def analyze_replay_trends(
    readiness_results: list[dict[str, Any]], audit_results: list[dict[str, Any]]
) -> dict[str, Any]:
    if not isinstance(readiness_results, list) or not isinstance(audit_results, list):
        return {
            "analysis_valid": False,
            "check_count": 0,
            "audit_count": 0,
            "ready_count": 0,
            "matched_count": 0,
            "readiness_rate": 0.0,
            "match_rate": 0.0,
            "replay_trend": "insufficient_data",
            "analysis_status": "invalid_input",
        }

    if len(readiness_results) == 0 and len(audit_results) == 0:
        return {
            "analysis_valid": True,
            "check_count": 0,
            "audit_count": 0,
            "ready_count": 0,
            "matched_count": 0,
            "readiness_rate": 0.0,
            "match_rate": 0.0,
            "replay_trend": "insufficient_data",
            "analysis_status": "empty",
        }

    check_count = len(readiness_results)
    audit_count = len(audit_results)
    ready_count = len(
        [r for r in readiness_results if isinstance(r, dict) and r.get("readiness_status") == "ready"]
    )
    matched_count = len(
        [r for r in audit_results if isinstance(r, dict) and r.get("audit_status") == "matched"]
    )
    readiness_rate = (
        round((ready_count / float(check_count)) * 100.0, 3) if check_count > 0 else 0.0
    )
    match_rate = round((matched_count / float(audit_count)) * 100.0, 3) if audit_count > 0 else 0.0

    if check_count < 2:
        trend = "insufficient_data"
    elif readiness_rate >= 80.0 and match_rate >= 80.0:
        trend = "reliable"
    elif readiness_rate < 50.0 or match_rate < 50.0:
        trend = "degraded"
    else:
        trend = "marginal"

    return {
        "analysis_valid": True,
        "check_count": check_count,
        "audit_count": audit_count,
        "ready_count": ready_count,
        "matched_count": matched_count,
        "readiness_rate": readiness_rate,
        "match_rate": match_rate,
        "replay_trend": trend,
        "analysis_status": "analyzed",
    }


def summarize_replay_trends(result: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(result, dict) or result.get("analysis_valid") is not True:
        return {
            "summary_valid": False,
            "analysis_status": "invalid_input",
            "replay_trend": "insufficient_data",
            "readiness_rate": 0.0,
        }

    return {
        "summary_valid": True,
        "analysis_status": result.get("analysis_status", "invalid_input"),
        "replay_trend": result.get("replay_trend", "insufficient_data"),
        "readiness_rate": float(result.get("readiness_rate", 0.0)),
    }
