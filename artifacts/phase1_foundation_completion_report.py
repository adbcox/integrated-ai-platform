from typing import Any

def generate_phase1_foundation_completion_report() -> dict[str, Any]:
    try:
        from framework.contract_retrieval_helpers import get_all_contracts_with_metadata
        from framework.metadata_aggregation import generate_metadata_overview, compute_metadata_coverage
        from framework.aggregation_summary_helpers import compute_completeness_score, get_aggregation_distribution_summary, identify_aggregation_gaps
        from framework.runtime_foundation_completeness import validate_runtime_foundation

        all_contracts = get_all_contracts_with_metadata()
        total_contracts = len(all_contracts)

        metadata_overview = generate_metadata_overview(all_contracts)
        coverage = compute_metadata_coverage(all_contracts)
        completeness_score = compute_completeness_score(coverage)

        field_stats = metadata_overview.get("field_statistics", {})
        distribution = get_aggregation_distribution_summary(field_stats)
        gaps = identify_aggregation_gaps(field_stats, total_contracts)

        foundation_validation = validate_runtime_foundation()

        return {
            "phase1_completion_report": "complete",
            "total_contracts_in_registry": total_contracts,
            "metadata_fields_found": metadata_overview.get("unique_metadata_fields", 0),
            "metadata_coverage_percent": coverage.get("coverage_percent", 0),
            "contracts_with_complete_metadata": completeness_score,
            "field_distribution_min": distribution.get("min_field_count", 0),
            "field_distribution_max": distribution.get("max_field_count", 0),
            "field_coverage_gaps_count": len(gaps),
            "runtime_foundation_completeness_percent": foundation_validation.get("completeness_percent", 0),
            "runtime_foundation_operational": foundation_validation.get("foundation_operational", False),
            "all_phase1_layers_present": foundation_validation.get("foundation_valid", False),
            "phase1_foundation_ready": foundation_validation.get("foundation_valid", False) and total_contracts > 0,
            "status": "complete"
        }
    except Exception as e:
        return {
            "phase1_completion_report": "error",
            "error_detail": str(e),
            "status": "failed"
        }
