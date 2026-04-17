from framework.schema_registry import SCHEMA_REGISTRY
from framework.runtime_contract_catalog_factory import build_runtime_contract_catalog
from framework.contract_coverage_analyzer import analyze_coverage
from framework.contract_grouping_helpers import group_by_category

def build_runtime_manifest():
    catalog = build_runtime_contract_catalog()
    coverage = analyze_coverage()
    categories = group_by_category()

    manifest = {
        "manifest_version": "1.0",
        "total_schema_entries": len(SCHEMA_REGISTRY),
        "schema_registry_checksum": "runtime_foundation_v1",
        "catalog_version": "1.0",
        "categories_defined": 5,
        "categories": {
            "session_contracts": len(catalog.session_contracts),
            "execution_contracts": len(catalog.execution_contracts),
            "validation_contracts": len(catalog.validation_contracts),
            "artifact_contracts": len(catalog.artifact_contracts),
            "routing_contracts": len(catalog.routing_contracts),
        },
        "modules_present": coverage["module_distribution"],
        "prefix_distribution": coverage["prefix_distribution"],
        "manifest_complete": True,
    }
    return manifest
