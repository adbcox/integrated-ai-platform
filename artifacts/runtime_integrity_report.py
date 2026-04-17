from typing import Any

def generate_runtime_integrity_report() -> dict[str, Any]:
    try:
        from framework.schema_registry import SCHEMA_REGISTRY
        from framework.runtime_contract_catalog_factory import build_runtime_contract_catalog
        from framework.contract_loader import create_loader
        from framework.runtime_manifest_builder import build_runtime_manifest
        from framework.manifest_query_engine import manifest_summary_stats

        registry_count = len(SCHEMA_REGISTRY)

        catalog = build_runtime_contract_catalog()
        catalog_total = (
            len(catalog.session_contracts) +
            len(catalog.execution_contracts) +
            len(catalog.validation_contracts) +
            len(catalog.artifact_contracts) +
            len(catalog.routing_contracts)
        )

        loader = create_loader()
        loader_access_works = loader.cache_size() >= 0

        manifest = build_runtime_manifest()
        manifest_stats = manifest_summary_stats(manifest)

        registry_catalog_aligned = registry_count == catalog_total
        catalog_manifest_aligned = catalog_total == manifest_stats.get("total_contracts", 0)
        all_layers_aligned = registry_catalog_aligned and catalog_manifest_aligned and loader_access_works

        return {
            "integrity_check_timestamp": "complete",
            "registry_schema_count": registry_count,
            "catalog_total_contracts": catalog_total,
            "manifest_total_contracts": manifest_stats.get("total_contracts", 0),
            "loader_accessible": loader_access_works,
            "registry_catalog_match": registry_catalog_aligned,
            "catalog_manifest_match": catalog_manifest_aligned,
            "all_layers_aligned": all_layers_aligned,
            "status": "complete",
        }
    except Exception as e:
        return {
            "integrity_check_timestamp": "error",
            "error_detail": str(e),
            "status": "failed",
        }
