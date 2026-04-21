"""MVP benchmark runner for Phase 3 developer-assistant (P3-01).

Runs at least 3 bounded synthetic task cases against the developer assistant loop
and returns a structured result set.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from framework.repo_intake_v1 import RepoIntakeV1
from framework.developer_task_v1 import DeveloperTaskV1
from framework.developer_assistant_loop_v1 import DeveloperAssistantLoopV1
from framework.workspace_controller_v1 import WorkspaceDescriptorV1
from framework.substrate_runtime_v1 import SubstrateRuntimeV1


@dataclass
class BenchmarkCaseResultV1:
    task_id: str
    task_kind: str
    passed: bool
    final_outcome: str
    failure_mode: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "task_kind": self.task_kind,
            "passed": self.passed,
            "final_outcome": self.final_outcome,
            "failure_mode": self.failure_mode,
        }


@dataclass
class BenchmarkSuiteResultV1:
    tasks_run: int
    tasks_passed: int
    pass_rate: float
    failure_modes: List[str]
    case_results: List[BenchmarkCaseResultV1] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "tasks_run": self.tasks_run,
            "tasks_passed": self.tasks_passed,
            "pass_rate": self.pass_rate,
            "failure_modes": self.failure_modes,
            "case_results": [c.to_dict() for c in self.case_results],
        }


_BENCHMARK_CASES = [
    DeveloperTaskV1(
        task_id="bench-001",
        objective="Inspect the repo intake module and confirm it is readable",
        task_kind="inspect",
        target_paths=["framework/repo_intake_v1.py"],
        validation_sequence=["file_readable", "workspace_valid"],
        retry_budget=1,
    ),
    DeveloperTaskV1(
        task_id="bench-002",
        objective="Inspect two substrate modules and validate workspace layout",
        task_kind="inspect",
        target_paths=["framework/substrate_runtime_v1.py", "framework/substrate_conformance_v1.py"],
        validation_sequence=["workspace_valid", "files_readable"],
        retry_budget=1,
    ),
    DeveloperTaskV1(
        task_id="bench-003",
        objective="Validate the Phase 2 baseline YAML is present and readable",
        task_kind="validate",
        target_paths=["governance/phase2_substrate_baseline.v1.yaml"],
        validation_sequence=["file_readable", "workspace_valid", "content_non_empty"],
        retry_budget=2,
    ),
    DeveloperTaskV1(
        task_id="bench-004",
        objective="Inspect the developer task module and result package module",
        task_kind="inspect",
        target_paths=["framework/developer_task_v1.py", "framework/result_package_v1.py"],
        validation_sequence=["files_readable", "workspace_valid"],
        retry_budget=1,
    ),
]


class MVPBenchmarkRunnerV1:
    def __init__(self, repo_root: str, scratch_root: str = "/tmp/mvp_benchmark") -> None:
        self.repo_root = repo_root
        desc = WorkspaceDescriptorV1(
            source_root=repo_root,
            scratch_root=scratch_root,
            artifact_root="artifacts/substrate",
            source_read_only=True,
        )
        self.runtime = SubstrateRuntimeV1(desc)
        self.loop = DeveloperAssistantLoopV1(self.runtime)

    def run(self, cases: Optional[List[DeveloperTaskV1]] = None) -> BenchmarkSuiteResultV1:
        cases = cases or _BENCHMARK_CASES
        case_results: List[BenchmarkCaseResultV1] = []
        failure_modes: List[str] = []

        for task in cases:
            intake = RepoIntakeV1(
                repo_root=self.repo_root,
                task_id=task.task_id,
                package_id="P3-01-DEVELOPER-ASSISTANT-MVP-PACK-1",
                package_label="SUBSTRATE",
                objective=task.objective,
                allowed_files=task.target_paths,
                forbidden_files=[],
            )
            try:
                loop_result = self.loop.run(intake, task)
                passed = loop_result.final_outcome == "success"
                failure_mode = None if passed else f"{task.task_id}: outcome={loop_result.final_outcome}"
            except Exception as exc:
                passed = False
                failure_mode = f"{task.task_id}: exception={exc}"

            if failure_mode:
                failure_modes.append(failure_mode)

            case_results.append(BenchmarkCaseResultV1(
                task_id=task.task_id,
                task_kind=task.task_kind,
                passed=passed,
                final_outcome=loop_result.final_outcome if "loop_result" in dir() else "error",
                failure_mode=failure_mode,
            ))

        tasks_run = len(case_results)
        tasks_passed = sum(1 for c in case_results if c.passed)
        pass_rate = tasks_passed / tasks_run if tasks_run > 0 else 0.0

        return BenchmarkSuiteResultV1(
            tasks_run=tasks_run,
            tasks_passed=tasks_passed,
            pass_rate=pass_rate,
            failure_modes=failure_modes,
            case_results=case_results,
        )
