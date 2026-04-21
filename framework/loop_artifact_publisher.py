"""LoopArtifactPublisher — adopts dispatch_publish_artifact for MVPLoopResult packaging.

Inspection gate output:
  dispatch_publish_artifact sig: (action: PublishArtifactAction, scope: ToolPathScope) -> PublishArtifactObservation
  PublishArtifactAction fields: ['artifact_path', 'destination']
  PublishArtifactObservation fields: ['artifact_path', 'destination', 'published', 'error']
  MVPLoopResult fields: ['task_kind', 'success', 'inspect_ok', 'patch_applied', 'test_passed',
                         'reverted', 'artifact_path', 'validation_artifact_path', 'error']
"""
from __future__ import annotations

import json
import tempfile
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from framework.mvp_coding_loop import MVPLoopResult
from framework.publish_artifact_dispatch import dispatch_publish_artifact
from framework.tool_schema import PublishArtifactAction
from framework.workspace_scope import ToolPathScope

assert callable(dispatch_publish_artifact), "INTERFACE MISMATCH: dispatch_publish_artifact not callable"
assert hasattr(MVPLoopResult, "__dataclass_fields__"), "INTERFACE MISMATCH: MVPLoopResult not dataclass"

_DEFAULT_ARTIFACT_DIR = Path("artifacts") / "loop_results"


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass
class LoopArtifactRecord:
    artifact_id: str
    task_kind: str
    target_path: str
    success: bool
    summary: str
    published_at: str
    artifact_path: str

    def to_dict(self) -> dict:
        return {
            "artifact_id": self.artifact_id,
            "task_kind": self.task_kind,
            "target_path": self.target_path,
            "success": self.success,
            "summary": self.summary,
            "published_at": self.published_at,
            "artifact_path": self.artifact_path,
        }


class LoopArtifactPublisher:
    """Publishes an MVPLoopResult as a named artifact via dispatch_publish_artifact."""

    def publish(
        self,
        loop_result: MVPLoopResult,
        *,
        artifact_dir: Optional[Path] = None,
        dry_run: bool = False,
    ) -> LoopArtifactRecord:
        artifact_id = str(uuid.uuid4())
        out_dir = Path(artifact_dir) if artifact_dir is not None else _DEFAULT_ARTIFACT_DIR
        task_kind = loop_result.task_kind or "unknown"
        success = bool(loop_result.success)
        summary = f"task_kind={task_kind} success={success} error={loop_result.error or 'none'}"
        target_path = loop_result.artifact_path or ""

        if dry_run:
            return LoopArtifactRecord(
                artifact_id=artifact_id,
                task_kind=task_kind,
                target_path=target_path,
                success=success,
                summary=summary,
                published_at=_iso_now(),
                artifact_path="",
            )

        out_dir.mkdir(parents=True, exist_ok=True)
        destination = out_dir / f"{artifact_id}.json"
        payload = {
            "schema_version": 1,
            "artifact_id": artifact_id,
            "task_kind": task_kind,
            "success": success,
            "summary": summary,
            "published_at": _iso_now(),
            "loop_result": {
                "task_kind": loop_result.task_kind,
                "success": loop_result.success,
                "error": loop_result.error,
            },
        }

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as tmp:
            json.dump(payload, tmp, indent=2)
            tmp_path = tmp.name

        try:
            scope = ToolPathScope(
                source_root=Path("."),
                writable_roots=(out_dir.resolve(),),
            )
            action = PublishArtifactAction(
                artifact_path=tmp_path,
                destination=str(destination),
            )
            obs = dispatch_publish_artifact(action, scope)
            published_path = str(destination) if obs.published else ""
        except Exception:  # noqa: BLE001
            published_path = ""
        finally:
            try:
                Path(tmp_path).unlink(missing_ok=True)
            except Exception:  # noqa: BLE001
                pass

        return LoopArtifactRecord(
            artifact_id=artifact_id,
            task_kind=task_kind,
            target_path=target_path,
            success=success,
            summary=summary,
            published_at=_iso_now(),
            artifact_path=published_path,
        )


__all__ = ["LoopArtifactRecord", "LoopArtifactPublisher"]
