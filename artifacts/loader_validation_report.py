from framework.contract_loader import create_loader
from framework.schema_registry import SCHEMA_REGISTRY

def generate_loader_validation_report():
    loader = create_loader()

    all_names = list(SCHEMA_REGISTRY.keys())
    sample_loaded = [loader.get_by_name(name) for name in all_names[:5]]
    all_samples_found = all(meta is not None for meta in sample_loaded)

    all_loaded = loader.get_all()
    all_loaded_count = len(all_loaded)
    all_loaded_complete = all(meta is not None for meta in all_loaded.values())

    initial_cache = loader.cache_size()
    loader.get_by_name(all_names[0])
    cached_lookup = loader.cache_size()
    cache_working = cached_lookup == initial_cache

    loader_valid = (
        all_samples_found and
        all_loaded_count == 99 and
        all_loaded_complete and
        cache_working
    )

    return {
        "total_contracts_loadable": all_loaded_count,
        "all_metadata_accessible": all_loaded_complete,
        "samples_found": all_samples_found,
        "cache_functional": cache_working,
        "loader_valid": loader_valid,
    }
