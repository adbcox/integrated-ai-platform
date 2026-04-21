"""LACE1-P5-ARTIFACT-PACKAGING-SEAM-1: typed artifact bundling surface."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from framework.artifact_manifest_schema import ArtifactManifest
from framework.artifact_package_result_schema import ArtifactPackageResult

assert "manifest_id" in ArtifactManifest.__dataclass_fields__, "INTERFACE MISMATCH: ArtifactManifest.manifest_id"
assert "result_id" in ArtifactPackageResult.__dataclass_fields__, "INTERFACE MISMATCH: ArtifactPackageResult.result_id"


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")


@dataclass
class BundledArtifact:
    bundle_id: str
    task_id: str
    diff_summary: str
    test_result_summary: str
    prose_summary: str
    source_paths: List[str]
    bundled_at: str
    artifact_path: Optional[str] = None


class ArtifactPackagingGate:
    """Bundles execution outputs into a single typed artifact."""

    def pack(
        self,
        *,
        task_id: str,
        diff_summary: str = "(no diff)",
        test_result_summary: str = "(no test result)",
        prose_summary: str,
        source_paths: List[str],
    ) -> BundledArtifact:
        bundle_id = f"BUNDLE-{task_id}-{_ts()}"
        return BundledArtifact(
            bundle_id=bundle_id,
            task_id=task_id,
            diff_summary=diff_summary,
            test_result_summary=test_result_summary,
            prose_summary=prose_summary,
            source_paths=list(source_paths),
            bundled_at=_iso_now(),
        )

    def emit(self, bundle: BundledArtifact, artifact_dir: Path) -> str:
        artifact_dir = Path(artifact_dir)
        artifact_dir.mkdir(parents=True, exist_ok=True)
        out_path = artifact_dir / f"{bundle.bundle_id}.json"
        out_path.write_text(
            json.dumps(
                {
                    "bundle_id": bundle.bundle_id,
                    "task_id": bundle.task_id,
                    "diff_summary": bundle.diff_summary,
                    "test_result_summary": bundle.test_result_summary,
                    "prose_summary": bundle.prose_summary,
                    "source_paths": bundle.source_paths,
                    "bundled_at": bundle.bundled_at,
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        bundle.artifact_path = str(out_path)
        return str(out_path)


__all__ = ["BundledArtifact", "ArtifactPackagingGate"]
