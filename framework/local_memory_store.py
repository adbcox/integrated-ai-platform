"""Local failure and repo-pattern memory store for the bounded coding loop.

Converts prior MVPCodingLoopRunner outcomes and validation records into
reusable local memory that improves first-pass quality for subsequent runs.

Two memory types:
  - FailurePattern: a recorded patch failure keyed by (task_kind, error_type)
  - SuccessPattern: a recorded success keyed by task_kind with the accepted
    (old_string_prefix, task_kind) fingerprint for reuse scoring

Memory is backed by append-only JSONL files under artifacts/local_memory/:
  failure_patterns.jsonl
  success_patterns.jsonl

Import-time interface assertions verify the ValidationRecord and
emit_validation_record shapes are as expected.
"""
from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from framework.validation_artifact_writer import ValidationCheck, ValidationRecord, emit_validation_record

# -- import-time interface assertions --
assert "emitter" in ValidationRecord.__dataclass_fields__, \
    "INTERFACE MISMATCH: ValidationRecord.emitter"
assert "outcome" in ValidationRecord.__dataclass_fields__, \
    "INTERFACE MISMATCH: ValidationRecord.outcome"
assert "check_name" in ValidationCheck.__dataclass_fields__, \
    "INTERFACE MISMATCH: ValidationCheck.check_name"
assert callable(emit_validation_record), \
    "INTERFACE MISMATCH: emit_validation_record not callable"

_DEFAULT_MEMORY_DIR = Path("artifacts") / "local_memory"
_ISO_FMT = "%Y-%m-%dT%H:%M:%SZ"


def _iso_now() -> str:
    return datetime.now(timezone.utc).strftime(_ISO_FMT)


def _classify_error(error: Optional[str]) -> str:
    """Map a raw error string to a normalized error_type token."""
    if not error:
        return "unknown"
    e = error.lower()
    if "not found" in e:
        return "old_string_not_found"
    if "permission" in e or "writable" in e:
        return "permission_denied"
    if "revert" in e:
        return "revert_failed"
    if "unsafe" in e or "task_kind" in e:
        return "unsafe_task_kind"
    if "inspect" in e or "read" in e:
        return "inspect_failed"
    if "test" in e or "exit_code" in e:
        return "test_failed"
    return "other"


@dataclass(frozen=True)
class FailurePattern:
    task_kind: str
    error_type: str
    error_summary: str
    target_file_suffix: str
    old_string_prefix: str
    recorded_at: str
    session_id: str = ""
    recurrence_count: int = 1

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "FailurePattern":
        return cls(
            task_kind=d.get("task_kind", ""),
            error_type=d.get("error_type", ""),
            error_summary=d.get("error_summary", ""),
            target_file_suffix=d.get("target_file_suffix", ""),
            old_string_prefix=d.get("old_string_prefix", ""),
            recorded_at=d.get("recorded_at", ""),
            session_id=d.get("session_id", ""),
            recurrence_count=int(d.get("recurrence_count", 1)),
        )


@dataclass(frozen=True)
class SuccessPattern:
    task_kind: str
    target_file_suffix: str
    old_string_prefix: str
    new_string_prefix: str
    recorded_at: str
    session_id: str = ""
    reuse_count: int = 1

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "SuccessPattern":
        return cls(
            task_kind=d.get("task_kind", ""),
            target_file_suffix=d.get("target_file_suffix", ""),
            old_string_prefix=d.get("old_string_prefix", ""),
            new_string_prefix=d.get("new_string_prefix", ""),
            recorded_at=d.get("recorded_at", ""),
            session_id=d.get("session_id", ""),
            reuse_count=int(d.get("reuse_count", 1)),
        )


def _file_suffix(path: str, *, n: int = 2) -> str:
    parts = Path(path).parts
    return "/".join(parts[-n:]) if len(parts) >= n else path


def _prefix(s: str, *, max_len: int = 80) -> str:
    stripped = s.strip()
    return stripped[:max_len] if len(stripped) > max_len else stripped


class LocalMemoryStore:
    """Append-only store for failure and success patterns.

    All writes are appended to JSONL files; reads scan the full file.
    The store is intentionally simple — no indexing, no deduplication on
    write. Callers use query methods to find relevant patterns.
    """

    def __init__(self, memory_dir: Optional[Path] = None) -> None:
        self._dir = Path(memory_dir) if memory_dir else (_DEFAULT_MEMORY_DIR)
        self._failure_path = self._dir / "failure_patterns.jsonl"
        self._success_path = self._dir / "success_patterns.jsonl"

    def _ensure_dir(self) -> None:
        self._dir.mkdir(parents=True, exist_ok=True)

    # -- write --

    def record_failure(
        self,
        *,
        task_kind: str,
        target_file: str,
        old_string: str,
        error: Optional[str],
        session_id: str = "",
    ) -> FailurePattern:
        """Append a failure pattern and return it."""
        pattern = FailurePattern(
            task_kind=task_kind,
            error_type=_classify_error(error),
            error_summary=_prefix(error or "unknown", max_len=200),
            target_file_suffix=_file_suffix(target_file),
            old_string_prefix=_prefix(old_string),
            recorded_at=_iso_now(),
            session_id=session_id,
        )
        self._ensure_dir()
        with self._failure_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(pattern.to_dict(), ensure_ascii=False) + "\n")
        return pattern

    def record_success(
        self,
        *,
        task_kind: str,
        target_file: str,
        old_string: str,
        new_string: str,
        session_id: str = "",
    ) -> SuccessPattern:
        """Append a success pattern and return it."""
        pattern = SuccessPattern(
            task_kind=task_kind,
            target_file_suffix=_file_suffix(target_file),
            old_string_prefix=_prefix(old_string),
            new_string_prefix=_prefix(new_string),
            recorded_at=_iso_now(),
            session_id=session_id,
        )
        self._ensure_dir()
        with self._success_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(pattern.to_dict(), ensure_ascii=False) + "\n")
        return pattern

    # -- read --

    def read_failures(self) -> list[FailurePattern]:
        """Return all recorded failure patterns (oldest first)."""
        return self._read_all(self._failure_path, FailurePattern.from_dict)

    def read_successes(self) -> list[SuccessPattern]:
        """Return all recorded success patterns (oldest first)."""
        return self._read_all(self._success_path, SuccessPattern.from_dict)

    def _read_all(self, path: Path, factory) -> list:
        if not path.exists():
            return []
        results = []
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                results.append(factory(json.loads(line)))
            except (json.JSONDecodeError, KeyError):
                continue
        return results

    # -- query --

    def query_failures(
        self,
        *,
        task_kind: Optional[str] = None,
        error_type: Optional[str] = None,
        limit: int = 10,
    ) -> list[FailurePattern]:
        """Return recent failures optionally filtered by task_kind / error_type."""
        patterns = self.read_failures()
        if task_kind:
            patterns = [p for p in patterns if p.task_kind == task_kind]
        if error_type:
            patterns = [p for p in patterns if p.error_type == error_type]
        return patterns[-limit:]

    def query_successes(
        self,
        *,
        task_kind: Optional[str] = None,
        limit: int = 10,
    ) -> list[SuccessPattern]:
        """Return recent successes optionally filtered by task_kind."""
        patterns = self.read_successes()
        if task_kind:
            patterns = [p for p in patterns if p.task_kind == task_kind]
        return patterns[-limit:]

    def failure_rate(self, task_kind: Optional[str] = None) -> float:
        """Return failure rate as fraction [0.0, 1.0] across stored patterns."""
        failures = len(self.query_failures(task_kind=task_kind, limit=10_000))
        successes = len(self.query_successes(task_kind=task_kind, limit=10_000))
        total = failures + successes
        if total == 0:
            return 0.0
        return failures / total

    def emit_memory_summary_record(
        self,
        *,
        session_id: str = "",
        dry_run: bool = False,
    ) -> Optional[str]:
        """Emit a ValidationRecord summarising current memory store state."""
        failures = self.read_failures()
        successes = self.read_successes()
        failure_rate = self.failure_rate()
        record = ValidationRecord(
            emitter="local_memory_store",
            validation_type="memory_summary",
            outcome="pass",
            checks=(
                ValidationCheck(
                    check_name="failure_patterns_count",
                    outcome="pass",
                    detail=str(len(failures)),
                ),
                ValidationCheck(
                    check_name="success_patterns_count",
                    outcome="pass",
                    detail=str(len(successes)),
                ),
                ValidationCheck(
                    check_name="failure_rate",
                    outcome="pass",
                    detail=f"{failure_rate:.3f}",
                ),
            ),
            session_id=session_id or None,
            notes=f"memory_dir={self._dir}",
        )
        return emit_validation_record(record, dry_run=dry_run)


def record_mvp_loop_outcome(
    result: Any,
    *,
    target_file: str,
    old_string: str,
    new_string: str,
    session_id: str = "",
    memory_dir: Optional[Path] = None,
) -> None:
    """Convenience function: record a MVPLoopResult into the local memory store.

    Accepts any object with .success, .task_kind, .error attributes — does
    not import MVPCodingLoopRunner to avoid circular imports.
    """
    store = LocalMemoryStore(memory_dir)
    task_kind = getattr(result, "task_kind", "text_replacement")
    success = getattr(result, "success", False)
    error = getattr(result, "error", None)

    if success:
        store.record_success(
            task_kind=task_kind,
            target_file=target_file,
            old_string=old_string,
            new_string=new_string,
            session_id=session_id,
        )
    else:
        store.record_failure(
            task_kind=task_kind,
            target_file=target_file,
            old_string=old_string,
            error=error,
            session_id=session_id,
        )


__all__ = [
    "FailurePattern",
    "SuccessPattern",
    "LocalMemoryStore",
    "record_mvp_loop_outcome",
]
