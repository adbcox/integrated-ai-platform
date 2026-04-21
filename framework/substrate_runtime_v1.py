"""Substrate runtime assembly helper for Phase 2 (P2-02).

Assembles the minimum substrate pieces from P2-01 and P2-02 into a small
runtime container. No integration into existing live runtime modules.
"""
from __future__ import annotations

from framework.tool_registry_v1 import ToolRegistryV1
from framework.tool_contracts_v1 import ToolContractV1
from framework.workspace_controller_v1 import WorkspaceDescriptorV1, WorkspaceControllerV1
from framework.permission_decision_v1 import PermissionDecisionV1, Decision
from framework.read_file_tool_v1 import ReadFileToolV1
from framework.publish_artifact_tool_v1 import PublishArtifactToolV1
from framework.run_command_tool_v1 import RunCommandToolV1
from framework.run_tests_tool_v1 import RunTestsToolV1


_TOOL_IMPLEMENTATIONS = {
    "read_file": ReadFileToolV1,
    "publish_artifact": PublishArtifactToolV1,
    "run_command": RunCommandToolV1,
    "run_tests": RunTestsToolV1,
}


class SubstrateRuntimeV1:
    """Minimum substrate runtime container. No live runtime integration."""

    def __init__(self, workspace: WorkspaceDescriptorV1) -> None:
        self.workspace_descriptor = workspace
        self.workspace_controller = WorkspaceControllerV1(workspace)
        self.tool_registry = ToolRegistryV1()
        self._tool_instances: dict = {
            name: cls() for name, cls in _TOOL_IMPLEMENTATIONS.items()
        }

    def get_tool(self, tool_name: str):
        return self._tool_instances.get(tool_name)

    def decide_permission(self, tool_name: str, target_scope: str) -> PermissionDecisionV1:
        contract = self.tool_registry.get_contract(tool_name)
        if contract is None:
            return PermissionDecisionV1(
                tool_name=tool_name,
                target_scope=target_scope,
                decision=Decision.DENY,
                rationale="tool not registered",
            )
        if contract.side_effecting:
            return PermissionDecisionV1(
                tool_name=tool_name,
                target_scope=target_scope,
                decision=Decision.ASK,
                rationale="side-effecting tool requires confirmation",
            )
        return PermissionDecisionV1(
            tool_name=tool_name,
            target_scope=target_scope,
            decision=Decision.ALLOW,
            rationale="read-only tool; allowed by default",
        )

    def is_ready(self) -> bool:
        return (
            self.workspace_controller.validate_layout()
            and len(self.tool_registry.list_tool_names()) >= 4
            and all(name in self._tool_instances for name in _TOOL_IMPLEMENTATIONS)
        )

    def summary(self) -> dict:
        return {
            "workspace_valid": self.workspace_controller.validate_layout(),
            "registered_tools": self.tool_registry.list_tool_names(),
            "tool_instances": list(self._tool_instances.keys()),
            "is_ready": self.is_ready(),
        }
