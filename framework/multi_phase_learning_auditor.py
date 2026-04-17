from typing import Any


def audit_learning(
    refinement: dict[str, Any],
    replay_learning: dict[str, Any],
    knowledge_validation: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(refinement, dict)
        or not isinstance(replay_learning, dict)
        or not isinstance(knowledge_validation, dict)
    ):
        return {
            "learning_audit_status": "invalid_input",
            "ok_count": 0,
            "audit_phase": None,
        }

    ref_ok = refinement.get("refinement_status") == "refined"
    replay_ok = replay_learning.get("replay_learning_status") == "learned"
    kv_ok = knowledge_validation.get("knowledge_validation_status") in ("valid", "partial")
    all_ok = ref_ok and replay_ok and kv_ok
    any_ok = ref_ok or replay_ok or kv_ok
    ok_count = sum([ref_ok, replay_ok, kv_ok])

    if all_ok:
        return {
            "learning_audit_status": "passed",
            "ok_count": ok_count,
            "audit_phase": refinement.get("refined_phase"),
        }

    if any_ok:
        return {
            "learning_audit_status": "degraded",
            "ok_count": ok_count,
            "audit_phase": None,
        }

    return {
        "learning_audit_status": "failed",
        "ok_count": ok_count,
        "audit_phase": None,
    }
