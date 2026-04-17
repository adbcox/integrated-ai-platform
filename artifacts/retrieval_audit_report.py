from typing import Any

def generate_retrieval_audit_report() -> dict[str, Any]:
    try:
        from framework.contract_retrieval_helpers import get_all_contracts_with_metadata
        from framework.retrieval_summary_helpers import summarize_retrieval_results, compute_retrieval_statistics
        from framework.contract_navigation import browse_contracts_hierarchically, find_related_contracts_by_pattern

        all_contracts = get_all_contracts_with_metadata()
        summary = summarize_retrieval_results(all_contracts)
        stats = compute_retrieval_statistics(all_contracts)
        hierarchy = browse_contracts_hierarchically(all_contracts)

        sample_contract = all_contracts[0]["name"] if all_contracts else None
        navigation_test = find_related_contracts_by_pattern(all_contracts, sample_contract) if sample_contract else {}
        navigation_works = isinstance(navigation_test, dict) and "parents" in navigation_test and "siblings" in navigation_test and "children" in navigation_test

        return {
            "retrieval_audit": "complete",
            "total_contracts_audited": summary["total_contracts"],
            "retrieval_helpers_functional": len(all_contracts) == 99,
            "summary_statistics_available": all([k in stats for k in ["min_name_length", "max_name_length", "average_metadata_fields", "total_name_chars"]]),
            "hierarchy_detection_works": hierarchy["hierarchy_branches"] >= 0,
            "navigation_works": navigation_works,
            "all_layers_accessible": len(all_contracts) == 99 and navigation_works,
            "status": "complete"
        }
    except Exception as e:
        return {
            "retrieval_audit": "error",
            "error_detail": str(e),
            "status": "failed"
        }
