from typing import Any


def rollup_evidence(
    evidence_collector: dict[str, Any],
    evidence_normalizer: dict[str, Any],
    evidence_hash_chainer: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(evidence_collector, dict)
        or not isinstance(evidence_normalizer, dict)
        or not isinstance(evidence_hash_chainer, dict)
    ):
        return {
            "evidence_rollup_status": "invalid_input",
            "rollup_phase": None,
            "rollup_count": 0,
        }

    ec_ok = evidence_collector.get("evidence_status") == "collected"
    en_ok = evidence_normalizer.get("normalization_status") == "normalized"
    chain_ok = evidence_hash_chainer.get("chain_status") == "chained"
    all_ok = ec_ok and en_ok and chain_ok

    if all_ok:
        return {
            "evidence_rollup_status": "rolled_up",
            "rollup_phase": evidence_collector.get("evidence_phase"),
            "rollup_count": evidence_hash_chainer.get("chain_length", 0),
        }

    if (ec_ok and en_ok) or (ec_ok and chain_ok) or (en_ok and chain_ok):
        return {
            "evidence_rollup_status": "degraded",
            "rollup_phase": None,
            "rollup_count": 0,
        }

    return {
        "evidence_rollup_status": "offline",
        "rollup_phase": None,
        "rollup_count": 0,
    }
