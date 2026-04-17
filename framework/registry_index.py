from framework.schema_registry import SCHEMA_REGISTRY

def build_registry_index():
    index_by_module = {}
    index_by_prefix = {}
    for class_name, path_str in SCHEMA_REGISTRY.items():
        module_name = path_str.split(':')[0]
        if module_name not in index_by_module:
            index_by_module[module_name] = []
        index_by_module[module_name].append(class_name)
        first_char = class_name[0] if class_name else ''
        if first_char not in index_by_prefix:
            index_by_prefix[first_char] = []
        index_by_prefix[first_char].append(class_name)
    sorted_by_module = {module: sorted(names) for module, names in sorted(index_by_module.items())}
    sorted_by_prefix = {prefix: sorted(names) for prefix, names in sorted(index_by_prefix.items())}
    return {
        "by_module": sorted_by_module,
        "by_prefix": sorted_by_prefix,
    }

def find_contracts_by_module(module):
    index = build_registry_index()
    return sorted(index["by_module"].get(module, []))

def find_contracts_by_prefix(prefix):
    index = build_registry_index()
    matching = [name for name in index["by_prefix"].get(prefix, []) if name.startswith(prefix)]
    return sorted(matching)

def contracts_per_module():
    index = build_registry_index()
    return {module: len(names) for module, names in sorted(index["by_module"].items())}
