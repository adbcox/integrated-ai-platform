from framework.schema_registry import SCHEMA_REGISTRY
from framework.contract_relationships import find_related_contracts

def get_contract_metadata(contract_name):
    if contract_name not in SCHEMA_REGISTRY:
        return None

    path_str = SCHEMA_REGISTRY[contract_name]
    module, class_path = path_str.split(':')
    related = find_related_contracts(contract_name)

    metadata = {
        "name": contract_name,
        "module": module,
        "class_path": class_path,
        "category": related["category"],
        "related_count": len(related["related"]),
        "related_in_category": related["related"],
        "metadata_complete": True,
    }
    return metadata

def enrich_all_contracts():
    enriched = {}
    for name in sorted(SCHEMA_REGISTRY.keys()):
        enriched[name] = get_contract_metadata(name)
    return enriched
