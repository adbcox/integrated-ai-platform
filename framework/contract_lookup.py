from typing import Optional
from framework.schema_registry import SCHEMA_REGISTRY
from framework.runtime_contract_catalog_factory import build_runtime_contract_catalog

def get_contract_by_name(name: str) -> Optional[dict[str, str]]:
    if name in SCHEMA_REGISTRY:
        return {"name": name, "path": SCHEMA_REGISTRY[name]}
    return None

def list_contracts_in_category(category: str) -> list[str]:
    catalog = build_runtime_contract_catalog()
    if hasattr(catalog, category):
        return sorted(getattr(catalog, category))
    return []

def all_contracts() -> dict[str, str]:
    return {k: SCHEMA_REGISTRY[k] for k in sorted(SCHEMA_REGISTRY.keys())}

def contract_exists(name: str) -> bool:
    return name in SCHEMA_REGISTRY
