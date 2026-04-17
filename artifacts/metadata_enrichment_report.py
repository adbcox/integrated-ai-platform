from framework.contract_metadata import enrich_all_contracts

def generate_metadata_enrichment_report():
    enriched = enrich_all_contracts()

    all_enriched = len(enriched)
    all_complete = all(meta["metadata_complete"] for meta in enriched.values())
    all_categorized = all(meta["category"] is not None for meta in enriched.values())

    related_counts = [meta["related_count"] for meta in enriched.values()]
    avg_related = sum(related_counts) / len(related_counts) if related_counts else 0

    metadata_valid = (
        all_enriched == 99 and
        all_complete and
        all_categorized
    )

    return {
        "total_contracts_enriched": all_enriched,
        "all_metadata_complete": all_complete,
        "all_contracts_categorized": all_categorized,
        "average_related_per_contract": round(avg_related, 2),
        "metadata_enrichment_valid": metadata_valid,
    }
