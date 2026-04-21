"""Minimal tool registry for the minimum substrate (Phase 2, P2-01)."""
from __future__ import annotations

from typing import Dict, List, Optional

from framework.tool_contracts_v1 import ToolContractV1, ALL_CONTRACTS


class ToolRegistryV1:
    def __init__(self) -> None:
        self._registry: Dict[str, ToolContractV1] = {}
        for contract in ALL_CONTRACTS:
            self._registry[contract.tool_name] = contract

    def list_tool_names(self) -> List[str]:
        return list(self._registry.keys())

    def get_contract(self, tool_name: str) -> Optional[ToolContractV1]:
        return self._registry.get(tool_name)

    def register(self, contract: ToolContractV1) -> None:
        self._registry[contract.tool_name] = contract
