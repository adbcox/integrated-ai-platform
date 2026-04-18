"""Offline regression for framework.runtime_artifact_service."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from framework.runtime_artifact_service import RuntimeArtifactService
from framework.runtime_telemetry_schema import (
    RUN_BUNDLE_SCHEMA_VERSION,
    CommandTelemetry,
    InferenceTelemetry,
    ValidationRecord,
)
from framework.runtime_workspace_contract import build_workspace


def _make_inference(prof: str = "fast", ok: bool = True) -> InferenceTelemetry:
    return InferenceTelemetry(
        profile_name=prof,
        backend="ollama",
        model="qwen2.5-coder:14b",
        timeout_seconds=90,
        retry_budget=1,
        prompt_hash="abc123",
        started_at="2026-04-18T00:00:00+00:00",
        completed_at="2026-04-18T00:00:01+00:00",
        duration_ms=1000,
        success=ok,
    )


def _make_command(ok: bool = True) -> CommandTelemetry:
    return CommandTelemetry(
        command="echo hi",
        cwd="/tmp",
        return_code=0 if ok else 1,
        stdout="hi\n" if ok else "",
        stderr="" if ok else "err",
        started_at="2026-04-18T00:00:00+00:00",
        completed_at="2026-04-18T00:00:01+00:00",
        duration_ms=1000,
        success=ok,
    )


class RuntimeArtifactServiceTest(unittest.TestCase):
    def test_build_and_write_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as src, tempfile.TemporaryDirectory() as base:
            ws = build_workspace(
                source_root=Path(src),
                base_root=Path(base),
                run_id="r1",
                session_id="s1",
            )
            svc = RuntimeArtifactService(ws)
            svc.record_inference(_make_inference("fast", True))
            svc.record_command(_make_command(True))
            svc.record_validation(ValidationRecord(name="ok", passed=True, detail="x"))
            # Record a side effect in scratch (allowed)
            ws.ensure_materialized()
            probe = ws.scratch_root / "side_effect.txt"
            probe.write_text("x", encoding="utf-8")
            svc.record_side_effect(probe)

            manifest = svc.build_manifest(
                profile_name="fast",
                final_outcome="completed",
                artifact_bundle_ref="run_bundle_manifest.json",
            )
            self.assertEqual(manifest.schema_version, RUN_BUNDLE_SCHEMA_VERSION)
            self.assertEqual(manifest.run_id, "r1")
            self.assertEqual(manifest.session_id, "s1")
            self.assertEqual(manifest.profile_name, "fast")
            self.assertEqual(manifest.final_outcome, "completed")
            self.assertEqual(len(manifest.inference_records), 1)
            self.assertEqual(len(manifest.command_records), 1)
            self.assertEqual(len(manifest.validation_records), 1)
            self.assertEqual(len(manifest.workspace_side_effects), 1)

            path = svc.write_manifest(manifest)
            self.assertTrue(path.exists())
            payload = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(payload["run_id"], "r1")
            self.assertEqual(payload["final_outcome"], "completed")

    def test_side_effect_in_source_root_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as src, tempfile.TemporaryDirectory() as base:
            ws = build_workspace(
                source_root=Path(src),
                base_root=Path(base),
                run_id="r1",
                session_id="s1",
            )
            svc = RuntimeArtifactService(ws)
            forbidden = Path(src) / "file.txt"
            with self.assertRaises(PermissionError):
                svc.record_side_effect(forbidden)


if __name__ == "__main__":
    unittest.main()
