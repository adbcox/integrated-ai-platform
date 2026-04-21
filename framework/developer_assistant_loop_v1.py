"""Substrate-backed developer assistant loop for Phase 3 MVP (P3-01).

Wires together repo intake, developer task, substrate runtime, and result package.
No live multi-step coding autonomy yet — executes bounded synthetic steps using
substrate types and produces structured output.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from framework.repo_intake_v1 import RepoIntakeV1
from framework.developer_task_v1 import DeveloperTaskV1
from framework.workspace_controller_v1 import WorkspaceDescriptorV1
from framework.substrate_runtime_v1 import SubstrateRuntimeV1


@dataclass
class LoopResultV1:
    task_id: str
    inspected_paths: List[str]
    validations_run: List[str]
    validation_results: dict
    final_outcome: str          # success | failure | escalated
    escalation_status: str
    artifacts_produced: List[str] = field(default_factory=list)
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "inspected_paths": self.inspected_paths,
            "validations_run": self.validations_run,
            "validation_results": self.validation_results,
            "final_outcome": self.final_outcome,
            "escalation_status": self.escalation_status,
            "artifacts_produced": self.artifacts_produced,
            "error": self.error,
        }


class DeveloperAssistantLoopV1:
    """Substrate-backed inspect/patch/validate loop."""

    def __init__(self, runtime: SubstrateRuntimeV1) -> None:
        self.runtime = runtime

    def run(
        self,
        intake: RepoIntakeV1,
        task: DeveloperTaskV1,
        artifact_dest: Optional[str] = None,
    ) -> LoopResultV1:
        inspected_paths: List[str] = []
        validations_run: List[str] = []
        validation_results: dict = {}
        artifacts_produced: List[str] = []

        # Step 1: inspect declared target paths
        read_tool = self.runtime.get_tool("read_file")
        for path in task.target_paths:
            full_path = str(Path(intake.repo_root) / path) if not Path(path).is_absolute() else path
            result = read_tool.run(full_path)
            inspected_paths.append(path)
            validation_results[f"inspect:{path}"] = result.status

        # Step 2: run validation sequence steps (synthetic: structure-only)
        for step in task.validation_sequence:
            validations_run.append(step)
            # Synthetic validation: pass if workspace is valid
            validation_results[step] = "pass" if self.runtime.workspace_controller.validate_layout() else "fail"

        # Step 3: emit result artifact if dest provided
        if artifact_dest:
            pub_tool = self.runtime.get_tool("publish_artifact")
            summary = {
                "task_id": task.task_id,
                "objective": task.objective,
                "task_kind": task.task_kind,
                "inspected_paths": inspected_paths,
                "validations_run": validations_run,
                "validation_results": validation_results,
                "escalation_status": "NOT_ESCALATED",
            }
            pub_result = pub_tool.run(artifact_dest, summary)
            if pub_result.status == "success":
                artifacts_produced.append(artifact_dest)

        all_pass = all(v == "pass" for k, v in validation_results.items() if not k.startswith("inspect:"))
        final_outcome = "success" if all_pass else "failure"

        return LoopResultV1(
            task_id=task.task_id,
            inspected_paths=inspected_paths,
            validations_run=validations_run,
            validation_results=validation_results,
            final_outcome=final_outcome,
            escalation_status="NOT_ESCALATED",
            artifacts_produced=artifacts_produced,
        )
