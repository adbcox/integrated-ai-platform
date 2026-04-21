"""LoopEvidenceBundle: ties together all per-run evidence from a single bounded loop run."""
from __future__ import annotations

import dataclasses
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from framework.search_aware_inspect import SearchAwareInspectResult
from framework.listdir_inspect_helper import TargetDiscoveryResult
from framework.diff_result_packager import DiffResultPackage
from framework.bounded_result_publisher import PublicationRecord
from framework.retry_telemetry import RetryTelemetryRecord

# -- import-time assertions --
assert "context_snippet" in SearchAwareInspectResult.__dataclass_fields__, \
    "INTERFACE MISMATCH: SearchAwareInspectResult.context_snippet"
assert "sibling_names" in TargetDiscoveryResult.__dataclass_fields__, \
    "INTERFACE MISMATCH: TargetDiscoveryResult.sibling_names"
assert "diff" in DiffResultPackage.__dataclass_fields__, \
    "INTERFACE MISMATCH: DiffResultPackage.diff"
assert "published" in PublicationRecord.__dataclass_fields__, \
    "INTERFACE MISMATCH: PublicationRecord.published"
assert "retry_eligible_failures" in RetryTelemetryRecord.__dataclass_fields__, \
    "INTERFACE MISMATCH: RetryTelemetryRecord.retry_eligible_failures"


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _to_dict_safe(obj: Any) -> Any:
    if obj is None:
        return None
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return dataclasses.asdict(obj)
    return str(obj)


@dataclass
class LoopEvidenceBundle:
    session_id: str
    built_at: str
    search_result: Optional[Dict[str, Any]] = field(default=None)
    discovery_result: Optional[Dict[str, Any]] = field(default=None)
    diff_package: Optional[Dict[str, Any]] = field(default=None)
    validation_record: Optional[Dict[str, Any]] = field(default=None)
    retry_telemetry: Optional[Dict[str, Any]] = field(default=None)
    publication_record: Optional[Dict[str, Any]] = field(default=None)


def build_evidence_bundle(
    session_id: str,
    *,
    search_result: Optional[SearchAwareInspectResult] = None,
    discovery_result: Optional[TargetDiscoveryResult] = None,
    diff_package: Optional[DiffResultPackage] = None,
    validation_record: Optional[Any] = None,
    retry_telemetry: Optional[RetryTelemetryRecord] = None,
    publication_record: Optional[PublicationRecord] = None,
) -> LoopEvidenceBundle:
    return LoopEvidenceBundle(
        session_id=session_id,
        built_at=_iso_now(),
        search_result=_to_dict_safe(search_result),
        discovery_result=_to_dict_safe(discovery_result),
        diff_package=_to_dict_safe(diff_package),
        validation_record=_to_dict_safe(validation_record),
        retry_telemetry=_to_dict_safe(retry_telemetry),
        publication_record=_to_dict_safe(publication_record),
    )


def emit_evidence_bundle(
    bundle: LoopEvidenceBundle,
    *,
    artifact_dir: Path = Path("artifacts") / "loop_evidence_bundles",
) -> str:
    artifact_dir = Path(artifact_dir)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    out_path = artifact_dir / f"bundle_{bundle.session_id}.json"
    out_path.write_text(
        json.dumps(dataclasses.asdict(bundle), indent=2, default=str),
        encoding="utf-8",
    )
    return str(out_path)


__all__ = ["LoopEvidenceBundle", "build_evidence_bundle", "emit_evidence_bundle"]
