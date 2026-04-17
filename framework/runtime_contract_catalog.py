from dataclasses import dataclass, field

@dataclass
class RuntimeContractCatalog:
    session_contracts: list[str] = field(default_factory=list)
    execution_contracts: list[str] = field(default_factory=list)
    validation_contracts: list[str] = field(default_factory=list)
    artifact_contracts: list[str] = field(default_factory=list)
    routing_contracts: list[str] = field(default_factory=list)
