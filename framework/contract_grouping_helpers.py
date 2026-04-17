from framework.contract_category_accessor import get_all_categories

def group_by_category():
    return {cat: sorted(names) for cat, names in sorted(get_all_categories().items())}

def group_by_module():
    from framework.registry_index import build_registry_index
    index = build_registry_index()
    return {module: sorted(names) for module, names in sorted(index["by_module"].items())}

def group_by_semantic_prefix():
    all_cats = get_all_categories()
    by_prefix = {}
    for names in all_cats.values():
        for name in names:
            prefix_len = 1
            while prefix_len < len(name) and name[prefix_len].isupper():
                prefix_len += 1
            semantic_prefix = name[:max(1, prefix_len)]
            if semantic_prefix not in by_prefix:
                by_prefix[semantic_prefix] = []
            by_prefix[semantic_prefix].append(name)
    return {prefix: sorted(names) for prefix, names in sorted(by_prefix.items())}
