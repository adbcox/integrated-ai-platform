from typing import Any


def record_witness(
    chain: dict[str, Any],
    self_eval_cp: dict[str, Any],
    witness_config: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(chain, dict)
        or not isinstance(self_eval_cp, dict)
        or not isinstance(witness_config, dict)
    ):
        return {
            "witness_status": "invalid_input",
            "witness_phase": None,
            "witness_count": 0,
        }

    chain_ok = chain.get("chain_status") == "chained"
    cp_ok = self_eval_cp.get("self_eval_cp_status") == "operational"
    all_ok = chain_ok and cp_ok

    if all_ok:
        return {
            "witness_status": "recorded",
            "witness_phase": chain.get("chain_phase"),
            "witness_count": chain.get("chain_length", 0),
        }

    return {
        "witness_status": "failed",
        "witness_phase": None,
        "witness_count": 0,
    }
