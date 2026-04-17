from typing import Any


def summarize_exit_readiness(
    exit_readiness_validator: dict[str, Any],
    self_evaluation_summary: dict[str, Any],
    benchmark_summary: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(exit_readiness_validator, dict)
        or not isinstance(self_evaluation_summary, dict)
        or not isinstance(benchmark_summary, dict)
    ):
        return {
            "exit_readiness_summary_status": "invalid_input",
            "summary_phase": None,
            "summary_level": None,
        }

    erv_ok = exit_readiness_validator.get("exit_readiness_status") == "valid"
    ses_ok = self_evaluation_summary.get("self_eval_summary_status") == "complete"
    bs_ok = benchmark_summary.get("benchmark_summary_status") == "complete"
    all_ok = erv_ok and ses_ok and bs_ok

    if all_ok:
        return {
            "exit_readiness_summary_status": "complete",
            "summary_phase": exit_readiness_validator.get("exit_phase"),
            "summary_level": "comprehensive",
        }

    if (erv_ok and ses_ok) or (erv_ok and bs_ok) or (ses_ok and bs_ok):
        return {
            "exit_readiness_summary_status": "partial",
            "summary_phase": None,
            "summary_level": None,
        }

    return {
        "exit_readiness_summary_status": "incomplete",
        "summary_phase": None,
        "summary_level": None,
    }
