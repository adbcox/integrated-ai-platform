from framework.schema_registry import SCHEMA_REGISTRY
from framework.contract_metadata import get_contract_metadata

class ContractLoader:
    def __init__(self):
        self._metadata_cache = {}

    def get_by_name(self, name):
        if name in self._metadata_cache:
            return self._metadata_cache[name]
        metadata = get_contract_metadata(name)
        if metadata:
            self._metadata_cache[name] = metadata
        return metadata

    def get_all(self):
        all_meta = {}
        for name in sorted(SCHEMA_REGISTRY.keys()):
            all_meta[name] = self.get_by_name(name)
        return all_meta

    def cache_size(self):
        return len(self._metadata_cache)

def create_loader():
    return ContractLoader()
