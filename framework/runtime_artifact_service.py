"""Phase 1 runtime artifact service.

Writes per-run bundle manifests under a ``RuntimeWorkspace``'s
``artifact_root``. The bundle shape is defined by
``framework.runtime_telemetry_schema.RunBundleManifest``.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .runtime_telemetry_schema import (
    RUN_BUNDLE_SCHEMA_VERSION,
    CommandTelemetry,
    InferenceTelemetry,
    RunBundleManifest,
    ValidationRecord,
)
from .runtime_workspace_contract import RuntimeWorkspace, assert_read_only_source


class RuntimeArtifactService:
    """Build and persist per-run bundle manifests."""

    def __init__(self, workspace: RuntimeWorkspace) -> None:
        self._workspace = workspace
        self._command_records: list[dict[str, Any]] = []
        self._validation_records: list[dict[str, Any]] = []
        self._inference_records: list[dict[str, Any]] = []
        self._workspace_side_effects: list[str] = []

    @property
    def workspace(self) -> RuntimeWorkspace:
        return self._workspace

    def record_inference(self, telemetry: InferenceTelemetry) -> None:
        self._inference_records.append(telemetry.to_dict())

    def record_command(self, telemetry: CommandTelemetry) -> None:
        self._command_records.append(telemetry.to_dict())

    def record_validation(self, record: ValidationRecord) -> None:
        self._validation_records.append(record.to_dict())

    def record_side_effect(self, path: Path) -> None:
        assert_read_only_source(self._workspace, path)
        self._workspace_side_effects.append(str(path))

    def build_manifest(
        self,
        *,
        profile_name: str,
        final_outcome: str,
        artifact_bundle_ref: str = "",
    ) -> RunBundleManifest:
        return RunBundleManifest(
            schema_version=RUN_BUNDLE_SCHEMA_VERSION,
            run_id=self._workspace.run_id,
            session_id=self._workspace.session_id,
            profile_name=profile_name,
            source_root=str(self._workspace.source_root),
            scratch_root=str(self._workspace.scratch_root),
            artifact_root=str(self._workspace.artifact_root),
            command_records=list(self._command_records),
            validation_records=list(self._validation_records),
            inference_records=list(self._inference_records),
            workspace_side_effects=list(self._workspace_side_effects),
            artifact_bundle_ref=artifact_bundle_ref,
            final_outcome=final_outcome,
        )

    def write_manifest(self, manifest: RunBundleManifest) -> Path:
        self._workspace.ensure_materialized()
        manifest_path = self._workspace.artifact_root / "run_bundle_manifest.json"
        payload = manifest.to_dict()
        manifest_path.write_text(
            json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        return manifest_path


__all__ = ["RuntimeArtifactService"]
