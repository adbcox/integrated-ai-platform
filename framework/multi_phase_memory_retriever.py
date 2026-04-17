from typing import Any


def retrieve_phase_memory(
    memory_store: dict[str, Any],
    query: dict[str, Any],
    retrieval_config: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(memory_store, dict)
        or not isinstance(query, dict)
        or not isinstance(retrieval_config, dict)
    ):
        return {
            "retrieval_status": "invalid_input",
            "retrieved_count": 0,
            "retrieved_phase": None,
        }

    store_ok = memory_store.get("memory_status") == "stored"
    query_valid = bool(query.get("query_id"))
    store_count = memory_store.get("stored_count", 0) if store_ok else 0

    if store_ok and query_valid and store_count > 0:
        return {
            "retrieval_status": "retrieved",
            "retrieved_count": store_count,
            "retrieved_phase": memory_store.get("memory_phase"),
        }

    if store_ok and query_valid and store_count == 0:
        return {
            "retrieval_status": "empty",
            "retrieved_count": 0,
            "retrieved_phase": None,
        }

    if not store_ok:
        return {
            "retrieval_status": "no_memory",
            "retrieved_count": 0,
            "retrieved_phase": None,
        }

    return {
        "retrieval_status": "invalid_input",
        "retrieved_count": 0,
        "retrieved_phase": None,
    }
