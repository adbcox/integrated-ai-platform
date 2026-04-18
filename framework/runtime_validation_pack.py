"""Phase 1 baseline local runtime validation pack.

Proves the Phase 1 local route works end to end:

1. resolve a model profile through the inference gateway,
2. materialize workspace + artifact roots,
3. run at least one local command through the wrapper,
4. emit normalized inference telemetry,
5. write a complete artifact bundle/report,
6. return success deterministically.

The gateway executor is injectable so this pack can run fully offline
in tests while still representing the real local-route shape.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .inference_gateway import (
    ExecutorFn,
    GatewayRequest,
    GatewayResponse,
    InferenceGateway,
)
from .local_command_runner import LocalCommandRunner
from .model_profiles import resolve_profile_for_task_class
from .runtime_artifact_service import RuntimeArtifactService
from .runtime_telemetry_schema import RunBundleManifest, ValidationRecord
from .runtime_workspace_contract import RuntimeWorkspace, build_workspace


DEFAULT_TASK_CLASS = "single_file_edit"
DEFAULT_PROMPT = (
    "Phase 1 baseline validation prompt: describe no changes; confirm "
    "gateway resolves profile, workspace materializes, and a local "
    "command completes successfully."
)
DEFAULT_COMMAND = ["python3", "-c", "print('phase1-local-runtime-ok')"]


@dataclass(frozen=True)
class ValidationPackResult:
    success: bool
    manifest_path: Path
    manifest: RunBundleManifest
    inference: GatewayResponse

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "manifest_path": str(self.manifest_path),
            "manifest": self.manifest.to_dict(),
            "inference": self.inference.to_dict(),
        }


def run_baseline_validation(
    *,
    source_root: Path,
    base_root: Path,
    run_id: str,
    session_id: str,
    task_class: str = DEFAULT_TASK_CLASS,
    prompt: str = DEFAULT_PROMPT,
    command: list[str] | str = DEFAULT_COMMAND,
    executor: ExecutorFn | None = None,
) -> ValidationPackResult:
    """Execute the Phase 1 baseline local runtime validation pack."""
    workspace: RuntimeWorkspace = build_workspace(
        source_root=source_root,
        base_root=base_root,
        run_id=run_id,
        session_id=session_id,
    ).ensure_materialized()

    artifact_service = RuntimeArtifactService(workspace)
    profile = resolve_profile_for_task_class(task_class)

    gateway = InferenceGateway(executor=executor)
    request = GatewayRequest(
        profile_name=profile.profile_name,
        prompt=prompt,
        context={"task_class": task_class, "run_id": run_id},
        requested_by="runtime_validation_pack",
    )
    response = gateway.invoke(request)
    artifact_service.record_inference(response.telemetry)
    artifact_service.record_validation(
        ValidationRecord(
            name="gateway_invocation",
            passed=response.success,
            detail=f"profile={response.profile_name} backend={response.backend}",
        )
    )

    runner = LocalCommandRunner()
    command_telemetry = runner.run(command, cwd=workspace.scratch_root)
    artifact_service.record_command(command_telemetry)
    artifact_service.record_validation(
        ValidationRecord(
            name="local_command",
            passed=command_telemetry.success,
            detail=f"return_code={command_telemetry.return_code}",
        )
    )

    # Materialize a small deterministic side-effect into scratch to
    # prove the workspace contract is live for writes.
    scratch_probe = workspace.scratch_root / "baseline_ok.txt"
    scratch_probe.write_text("phase1-local-runtime-ok\n", encoding="utf-8")
    artifact_service.record_side_effect(scratch_probe)

    overall_success = response.success and command_telemetry.success
    manifest = artifact_service.build_manifest(
        profile_name=profile.profile_name,
        final_outcome="completed" if overall_success else "failed",
        artifact_bundle_ref="run_bundle_manifest.json",
    )
    manifest_path = artifact_service.write_manifest(manifest)

    return ValidationPackResult(
        success=overall_success,
        manifest_path=manifest_path,
        manifest=manifest,
        inference=response,
    )


__all__ = [
    "DEFAULT_COMMAND",
    "DEFAULT_PROMPT",
    "DEFAULT_TASK_CLASS",
    "ValidationPackResult",
    "run_baseline_validation",
]
