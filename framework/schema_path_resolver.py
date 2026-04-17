from framework.schema_registry import SCHEMA_REGISTRY

def get_schema_path_map() -> dict[str, str]:
    return {k: SCHEMA_REGISTRY[k] for k in sorted(SCHEMA_REGISTRY.keys())}
