from typing import Any

def get_contract_with_metadata(contract_name: str) -> dict[str, Any]:
    try:
        from framework.contract_loader import ContractLoader
        loader = ContractLoader()
        metadata = loader.get_by_name(contract_name)
        if metadata is None:
            return {}
        return {"name": contract_name, "metadata": metadata}
    except Exception:
        return {}

def get_all_contracts_with_metadata() -> list[dict[str, Any]]:
    try:
        from framework.contract_loader import ContractLoader
        loader = ContractLoader()
        all_contracts = loader.get_all()
        result = []
        for contract_name in sorted(all_contracts.keys()):
            metadata = all_contracts[contract_name]
            result.append({"name": contract_name, "metadata": metadata})
        return result
    except Exception:
        return []

def get_contracts_in_category_with_stats(category: str) -> dict[str, Any]:
    try:
        from framework.contract_category_accessor import get_category_contracts
        from framework.contract_loader import ContractLoader
        loader = ContractLoader()
        names = get_category_contracts(category)
        contracts = []
        for contract_name in sorted(names):
            metadata = loader.get_by_name(contract_name)
            contracts.append({"name": contract_name, "metadata": metadata})
        return {
            "category": category,
            "count": len(contracts),
            "contracts": contracts,
        }
    except Exception:
        return {"category": category, "count": 0, "contracts": []}

def get_contracts_by_module_prefix(prefix: str) -> list[dict[str, Any]]:
    try:
        from framework.contract_loader import ContractLoader
        loader = ContractLoader()
        all_contracts = loader.get_all()
        result = []
        for contract_name in sorted(all_contracts.keys()):
            metadata = all_contracts[contract_name]
            module_name = metadata.get("module", "") if isinstance(metadata, dict) else ""
            if module_name.startswith(prefix):
                result.append({"name": contract_name, "metadata": metadata})
        return result
    except Exception:
        return []
