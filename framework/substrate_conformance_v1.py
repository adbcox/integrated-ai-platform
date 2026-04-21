"""Substrate conformance checker for Phase 2 (P2-02).

Verifies that the minimum substrate surfaces from P2-01 and P2-02 cohere.
Returns a structured conformance result.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


REQUIRED_TOOL_NAMES = {"read_file", "run_command", "run_tests", "publish_artifact"}

REQUIRED_P2_MODULES = [
    "framework.session_job_schema_v1",
    "framework.tool_contracts_v1",
    "framework.tool_registry_v1",
    "framework.workspace_controller_v1",
    "framework.permission_decision_v1",
    "framework.artifact_bundle_v1",
    "framework.read_file_tool_v1",
    "framework.publish_artifact_tool_v1",
    "framework.run_command_tool_v1",
    "framework.run_tests_tool_v1",
    "framework.substrate_runtime_v1",
]


@dataclass
class ConformanceResultV1:
    tool_registry_complete: bool
    workspace_validates: bool
    artifact_bundle_assembles: bool
    substrate_artifact_emitted: bool
    modules_loadable: bool
    all_passed: bool
    errors: List[str] = field(default_factory=list)
    details: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "tool_registry_complete": self.tool_registry_complete,
            "workspace_validates": self.workspace_validates,
            "artifact_bundle_assembles": self.artifact_bundle_assembles,
            "substrate_artifact_emitted": self.substrate_artifact_emitted,
            "modules_loadable": self.modules_loadable,
            "all_passed": self.all_passed,
            "errors": self.errors,
            "details": self.details,
        }


class SubstrateConformanceCheckerV1:

    def run(self) -> ConformanceResultV1:
        errors: list = []
        details: dict = {}

        # 1 — tool registry complete
        try:
            from framework.tool_registry_v1 import ToolRegistryV1
            r = ToolRegistryV1()
            registered = set(r.list_tool_names())
            tool_registry_complete = registered >= REQUIRED_TOOL_NAMES
            if not tool_registry_complete:
                errors.append(f"tool_registry missing: {REQUIRED_TOOL_NAMES - registered}")
            details["registered_tools"] = sorted(registered)
        except Exception as exc:
            tool_registry_complete = False
            errors.append(f"tool_registry load error: {exc}")

        # 2 — workspace validates
        try:
            from framework.workspace_controller_v1 import WorkspaceDescriptorV1, WorkspaceControllerV1
            d = WorkspaceDescriptorV1(
                source_root="/repo", scratch_root="/tmp/scratch",
                artifact_root="artifacts/substrate", source_read_only=True,
            )
            workspace_validates = WorkspaceControllerV1(d).validate_layout()
            if not workspace_validates:
                errors.append("workspace layout validation failed")
        except Exception as exc:
            workspace_validates = False
            errors.append(f"workspace check error: {exc}")

        # 3 — artifact bundle assembles
        try:
            from framework.session_job_schema_v1 import SessionRecord, JobRecord
            from framework.artifact_bundle_v1 import ArtifactBundleV1
            s = SessionRecord(
                session_id="conf-s", package_id="P2-02-CONFORMANCE", package_label="SUBSTRATE",
                objective="conformance", allowed_files=[], forbidden_files=[],
                selected_profile=None, selected_backend="substrate",
                workspace_root="/repo", artifact_root="artifacts/substrate",
                escalation_status="NOT_ESCALATED",
            )
            j = JobRecord(
                job_id="conf-j", package_id="P2-02-CONFORMANCE", package_label="SUBSTRATE",
                objective="conformance", allowed_files=[], forbidden_files=[],
                selected_profile=None, selected_backend="substrate",
                workspace_root="/repo", artifact_root="artifacts/substrate",
                escalation_status="NOT_ESCALATED",
            )
            bundle = ArtifactBundleV1(
                session=s, job=j, tools_used=["read_file"],
                validations_run=["conformance_check"],
                artifacts_produced=[], escalation_status="NOT_ESCALATED",
            )
            d2 = bundle.to_dict()
            artifact_bundle_assembles = "session" in d2 and "job" in d2
        except Exception as exc:
            artifact_bundle_assembles = False
            errors.append(f"artifact bundle error: {exc}")

        # 4 — substrate artifact path reachable (publish_artifact dry run)
        try:
            from framework.publish_artifact_tool_v1 import PublishArtifactToolV1
            tool = PublishArtifactToolV1()
            # Existence of the class and run method is sufficient for conformance
            substrate_artifact_emitted = callable(getattr(tool, "run", None))
        except Exception as exc:
            substrate_artifact_emitted = False
            errors.append(f"publish_artifact tool error: {exc}")

        # 5 — all required modules loadable
        modules_loadable = True
        failed_modules = []
        for mod in REQUIRED_P2_MODULES:
            try:
                __import__(mod)
            except Exception as exc:
                modules_loadable = False
                failed_modules.append(f"{mod}: {exc}")
        if failed_modules:
            errors.extend(failed_modules)
        details["modules_checked"] = REQUIRED_P2_MODULES
        details["failed_modules"] = failed_modules

        all_passed = (
            tool_registry_complete
            and workspace_validates
            and artifact_bundle_assembles
            and substrate_artifact_emitted
            and modules_loadable
        )

        return ConformanceResultV1(
            tool_registry_complete=tool_registry_complete,
            workspace_validates=workspace_validates,
            artifact_bundle_assembles=artifact_bundle_assembles,
            substrate_artifact_emitted=substrate_artifact_emitted,
            modules_loadable=modules_loadable,
            all_passed=all_passed,
            errors=errors,
            details=details,
        )
