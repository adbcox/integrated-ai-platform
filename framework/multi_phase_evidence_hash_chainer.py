from typing import Any


def chain_evidence_hashes(
    normalization: dict[str, Any],
    prior_hash: dict[str, Any],
    chainer_config: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(normalization, dict)
        or not isinstance(prior_hash, dict)
        or not isinstance(chainer_config, dict)
    ):
        return {
            "chain_status": "invalid_input",
            "chain_phase": None,
            "chain_length": 0,
            "chain_head": None,
        }

    norm_ok = normalization.get("normalization_status") == "normalized"

    if norm_ok:
        chain_length = int(prior_hash.get("length", 0)) + 1
        return {
            "chain_status": "chained",
            "chain_phase": normalization.get("normalization_phase"),
            "chain_length": chain_length,
            "chain_head": prior_hash.get("head"),
        }

    return {
        "chain_status": "failed",
        "chain_phase": None,
        "chain_length": 0,
        "chain_head": None,
    }
