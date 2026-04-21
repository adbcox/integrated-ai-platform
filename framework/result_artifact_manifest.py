"""ResultArtifactManifest: session-level index of all LoopEvidenceBundle artifact paths."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from framework.loop_evidence_bundle import LoopEvidenceBundle

# -- import-time assertion --
assert "session_id" in LoopEvidenceBundle.__dataclass_fields__, \
    "INTERFACE MISMATCH: LoopEvidenceBundle.session_id"


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass
class ResultArtifactManifest:
    session_id: str
    bundle_paths: List[str]
    bundle_count: int
    existing_count: int
    success_count: int
    built_at: str


def build_manifest(
    session_id: str,
    bundle_paths: Optional[List[str]] = None,
) -> ResultArtifactManifest:
    paths = list(bundle_paths or [])
    existing = [p for p in paths if Path(p).exists()]
    # Conservative success count: only count paths that exist
    success_count = len(existing)
    return ResultArtifactManifest(
        session_id=session_id,
        bundle_paths=paths,
        bundle_count=len(paths),
        existing_count=len(existing),
        success_count=success_count,
        built_at=_iso_now(),
    )


def emit_manifest(
    manifest: ResultArtifactManifest,
    *,
    artifact_dir: Path = Path("artifacts") / "result_manifests",
) -> str:
    artifact_dir = Path(artifact_dir)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    out_path = artifact_dir / f"manifest_{manifest.session_id}.json"
    out_path.write_text(
        json.dumps(
            {
                "session_id": manifest.session_id,
                "bundle_paths": manifest.bundle_paths,
                "bundle_count": manifest.bundle_count,
                "existing_count": manifest.existing_count,
                "success_count": manifest.success_count,
                "built_at": manifest.built_at,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return str(out_path)


__all__ = ["ResultArtifactManifest", "build_manifest", "emit_manifest"]
