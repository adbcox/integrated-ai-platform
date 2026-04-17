from framework.contract_category_accessor import get_all_categories

def find_related_contracts(contract_name):
    all_cats = get_all_categories()
    for category, names in all_cats.items():
        if contract_name in names:
            related = [n for n in names if n != contract_name]
            return {"category": category, "related": sorted(related)}
    return {"category": None, "related": []}

def category_members_count():
    all_cats = get_all_categories()
    return {cat: len(names) for cat, names in sorted(all_cats.items())}

def contracts_sharing_module_prefix(prefix):
    all_cats = get_all_categories()
    matching = []
    for names in all_cats.values():
        for name in names:
            if name.startswith(prefix):
                matching.append(name)
    return sorted(matching)
