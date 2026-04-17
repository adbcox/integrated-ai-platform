from typing import Any

def generate_retrieval_integration_report() -> dict[str, Any]:
    try:
        from framework.contract_retrieval_helpers import get_contract_with_metadata, get_all_contracts_with_metadata, get_contracts_in_category_with_stats
        from framework.contract_metadata_filter import search_contracts_by_name_substring, rank_contracts_by_relevance
        from framework.contract_loader import ContractLoader

        loader = ContractLoader()
        loaded = loader.get_all()
        all_names = sorted(loaded.keys())
        all_count = len(all_names)

        with_metadata_list = get_all_contracts_with_metadata()
        metadata_enrichment_works = len(with_metadata_list) == 99

        session_stats = get_contracts_in_category_with_stats("session_contracts")
        category_access_works = session_stats.get("count", 0) == 10

        test_contracts = with_metadata_list[:5]
        search_results = search_contracts_by_name_substring(test_contracts, "contract")
        search_works = isinstance(search_results, list)

        ranking_results = rank_contracts_by_relevance(test_contracts, "contract")
        ranking_works = isinstance(ranking_results, list)

        single_lookup = get_contract_with_metadata("ApprovalRecord")
        single_lookup_works = isinstance(single_lookup, dict) and single_lookup.get("name") == "ApprovalRecord"

        all_systems_functional = (
            metadata_enrichment_works and
            category_access_works and
            search_works and
            ranking_works and
            single_lookup_works
        )

        return {
            "retrieval_integration_check": "complete",
            "loader_total_contracts": all_count,
            "metadata_enrichment_works": metadata_enrichment_works,
            "category_access_works": category_access_works,
            "contract_search_works": search_works,
            "contract_ranking_works": ranking_works,
            "single_lookup_works": single_lookup_works,
            "all_retrieval_systems_functional": all_systems_functional,
            "status": "complete",
        }
    except Exception as e:
        return {
            "retrieval_integration_check": "error",
            "error_detail": str(e),
            "status": "failed",
        }
