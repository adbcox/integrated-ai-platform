from typing import Any

def generate_navigation_lineage_report() -> dict[str, Any]:
    try:
        from framework.contract_retrieval_helpers import get_all_contracts_with_metadata
        from framework.contract_navigation import get_contract_lineage
        from framework.navigation_summary_helpers import generate_lineage_report, get_deepest_lineage
        from framework.metadata_aggregation import generate_metadata_overview, compute_metadata_coverage

        all_contracts = get_all_contracts_with_metadata()
        if not all_contracts:
            return {"status": "failed", "reason": "no_contracts"}

        lineages = []
        for item in all_contracts[:20]:
            if isinstance(item, dict) and item.get("name"):
                lineage = get_contract_lineage(all_contracts, item["name"])
                if isinstance(lineage, dict):
                    lineages.append(lineage)

        lineage_report = generate_lineage_report(lineages)
        deepest = get_deepest_lineage(lineages)
        metadata_overview = generate_metadata_overview(all_contracts)
        coverage = compute_metadata_coverage(all_contracts)

        navigation_works = len(lineages) > 0
        aggregation_works = metadata_overview.get("unique_metadata_fields", 0) > 0

        return {
            "navigation_lineage_check": "complete",
            "total_contracts_analyzed": len(all_contracts),
            "lineages_computed": len(lineages),
            "deepest_lineage_depth": deepest.get("depth", 0),
            "total_parent_relationships": lineage_report.get("total_parent_relationships", 0),
            "total_child_relationships": lineage_report.get("total_child_relationships", 0),
            "metadata_fields_found": metadata_overview.get("unique_metadata_fields", 0),
            "metadata_coverage_percent": coverage.get("coverage_percent", 0),
            "navigation_works": navigation_works,
            "aggregation_works": aggregation_works,
            "all_layers_accessible": navigation_works and aggregation_works,
            "status": "complete"
        }
    except Exception as e:
        return {
            "navigation_lineage_check": "error",
            "error_detail": str(e),
            "status": "failed"
        }
