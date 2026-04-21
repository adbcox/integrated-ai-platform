"""Append-only canonical validation artifact emitter.

Writes machine-readable validation records to:
  artifacts/framework/validation/records.jsonl  — append-only, one JSON line per call
  artifacts/framework/validation/latest.json    — overwritten to mirror most recent record

Format contract: governance/validation_artifact_spec.json
Schema version:  1.0.0

Stdlib-only module. No imports from other framework modules.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from uuid import uuid4

REPO_ROOT: Path = Path(__file__).resolve().parent.parent
_DEFAULT_ARTIFACT_SUBDIR = Path("artifacts") / "framework" / "validation"
_SCHEMA_VERSION = "1.0.0"


@dataclass(frozen=True)
class ValidationCheck:
    check_name: str
    outcome: str
    detail: Optional[str] = None


@dataclass(frozen=True)
class ValidationRecord:
    emitter: str
    validation_type: str
    outcome: str
    checks: tuple[ValidationCheck, ...] = ()
    session_id: Optional[str] = None
    job_id: Optional[str] = None
    artifact_refs: tuple[str, ...] = ()
    notes: Optional[str] = None


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _make_record_id() -> str:
    return f"val-{uuid4().hex[:8]}"


def _serialise(record: ValidationRecord, record_id: str, emitted_at: str) -> dict:
    return {
        "record_id": record_id,
        "schema_version": _SCHEMA_VERSION,
        "emitted_at": emitted_at,
        "emitter": record.emitter,
        "validation_type": record.validation_type,
        "outcome": record.outcome,
        "session_id": record.session_id,
        "job_id": record.job_id,
        "checks": [asdict(c) for c in record.checks],
        "artifact_refs": list(record.artifact_refs),
        "notes": record.notes,
    }


def emit_validation_record(
    record: ValidationRecord,
    *,
    repo_root: Path = REPO_ROOT,
    artifact_dir: Optional[Path] = None,
    dry_run: bool = False,
) -> Optional[str]:
    """Append one validation record to records.jsonl and overwrite latest.json.

    Returns the path to the records.jsonl file on success, or None on dry_run.
    Re-raises OSError with added context if the directory cannot be created or
    files cannot be written.
    """
    if dry_run:
        return None

    base = artifact_dir if artifact_dir is not None else (repo_root / _DEFAULT_ARTIFACT_SUBDIR)

    try:
        base.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise OSError(
            f"validation_artifact_writer: cannot create output dir {base}: {exc}"
        ) from exc

    record_id = _make_record_id()
    emitted_at = _now_iso()
    payload = _serialise(record, record_id, emitted_at)
    line = json.dumps(payload, ensure_ascii=False, sort_keys=True)

    jsonl_path = base / "records.jsonl"
    latest_path = base / "latest.json"

    try:
        with jsonl_path.open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")
        latest_path.write_text(
            json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
    except OSError as exc:
        raise OSError(
            f"validation_artifact_writer: cannot write to {base}: {exc}"
        ) from exc

    return str(jsonl_path)


__all__ = [
    "ValidationCheck",
    "ValidationRecord",
    "emit_validation_record",
]
