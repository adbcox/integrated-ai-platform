from typing import Any


def analyze_throughput(report_results: list[dict[str, Any]]) -> dict[str, Any]:
    if not isinstance(report_results, list):
        return {
            "analysis_valid": False,
            "workflow_count": 0,
            "total_jobs_all": 0,
            "total_completed_all": 0,
            "total_elapsed_all": 0.0,
            "mean_throughput": 0.0,
            "peak_throughput": 0.0,
            "min_throughput": 0.0,
            "analysis_status": "invalid_input",
        }

    valid_reports = [
        r for r in report_results
        if isinstance(r, dict) and r.get("report_valid") is True
    ]

    if not valid_reports:
        return {
            "analysis_valid": True,
            "workflow_count": 0,
            "total_jobs_all": 0,
            "total_completed_all": 0,
            "total_elapsed_all": 0.0,
            "mean_throughput": 0.0,
            "peak_throughput": 0.0,
            "min_throughput": 0.0,
            "analysis_status": "empty",
        }

    throughputs = [
        float(r.get("throughput_jobs_per_sec", 0.0)) for r in valid_reports
    ]

    return {
        "analysis_valid": True,
        "workflow_count": len(valid_reports),
        "total_jobs_all": sum(int(r.get("total_jobs", 0)) for r in valid_reports),
        "total_completed_all": sum(
            int(r.get("completed_count", 0)) for r in valid_reports
        ),
        "total_elapsed_all": round(
            sum(float(r.get("elapsed_seconds", 0.0)) for r in valid_reports), 3
        ),
        "mean_throughput": round(
            sum(throughputs) / float(len(throughputs)), 3
        ),
        "peak_throughput": round(max(throughputs), 3),
        "min_throughput": round(min(throughputs), 3),
        "analysis_status": "analyzed",
    }


def summarize_throughput_analysis(result: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(result, dict) or result.get("analysis_valid") is not True:
        return {
            "summary_valid": False,
            "analysis_status": "invalid_input",
            "mean_throughput": 0.0,
            "workflow_count": 0,
        }

    return {
        "summary_valid": True,
        "analysis_status": result.get("analysis_status", "invalid_input"),
        "mean_throughput": float(result.get("mean_throughput", 0.0)),
        "workflow_count": int(result.get("workflow_count", 0)),
    }
