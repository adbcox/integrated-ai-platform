from framework.runtime_contract_catalog_factory import build_runtime_contract_catalog

def get_category_contracts(category: str) -> list[str]:
    catalog = build_runtime_contract_catalog()
    valid_categories = {
        "session_contracts",
        "execution_contracts",
        "validation_contracts",
        "artifact_contracts",
        "routing_contracts",
    }
    if category not in valid_categories:
        return []
    return sorted(getattr(catalog, category))

def get_all_categories() -> dict[str, list[str]]:
    catalog = build_runtime_contract_catalog()
    return {
        "session_contracts": sorted(catalog.session_contracts),
        "execution_contracts": sorted(catalog.execution_contracts),
        "validation_contracts": sorted(catalog.validation_contracts),
        "artifact_contracts": sorted(catalog.artifact_contracts),
        "routing_contracts": sorted(catalog.routing_contracts),
    }
