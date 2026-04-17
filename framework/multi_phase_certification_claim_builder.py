from typing import Any


def build_certification_claim(
    witness: dict[str, Any],
    benchmark_summary: dict[str, Any],
    claim_config: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(witness, dict)
        or not isinstance(benchmark_summary, dict)
        or not isinstance(claim_config, dict)
    ):
        return {
            "claim_status": "invalid_input",
            "claim_phase": None,
            "claim_count": 0,
        }

    wit_ok = witness.get("witness_status") == "recorded"
    bs_ok = benchmark_summary.get("benchmark_summary_status") == "complete"

    if wit_ok and bs_ok:
        return {
            "claim_status": "built",
            "claim_phase": witness.get("witness_phase"),
            "claim_count": witness.get("witness_count", 0),
        }

    return {
        "claim_status": "failed",
        "claim_phase": None,
        "claim_count": 0,
    }
