"""Repo-pattern library artifact for reusable success pattern recall.

Groups SuccessPattern records from LocalMemoryStore by (task_kind, target_file_suffix,
old_string_prefix), aggregates reuse_count, and persists as a queryable JSON artifact.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from framework.local_memory_store import LocalMemoryStore, SuccessPattern

# -- import-time assertion --
assert callable(LocalMemoryStore.query_successes), "INTERFACE MISMATCH: LocalMemoryStore.query_successes"
assert "reuse_count" in SuccessPattern.__dataclass_fields__, \
    "INTERFACE MISMATCH: SuccessPattern.reuse_count"
assert "target_file_suffix" in SuccessPattern.__dataclass_fields__, \
    "INTERFACE MISMATCH: SuccessPattern.target_file_suffix"

_DEFAULT_ARTIFACT_DIR = Path("artifacts") / "repo_patterns"


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass(frozen=True)
class PatternEntry:
    task_kind: str
    target_file_suffix: str
    old_string_prefix: str
    new_string_prefix: str
    reuse_count: int
    recorded_at: str


@dataclass
class RepoPatternLibrary:
    entries: list[PatternEntry] = field(default_factory=list)
    built_at: str = field(default_factory=_iso_now)
    total_patterns: int = 0

    def query(
        self,
        *,
        task_kind: Optional[str] = None,
        target_file_suffix: Optional[str] = None,
        top_n: int = 10,
    ) -> list[PatternEntry]:
        results = self.entries
        if task_kind is not None:
            results = [e for e in results if e.task_kind == task_kind]
        if target_file_suffix is not None:
            results = [e for e in results if e.target_file_suffix == target_file_suffix]
        return sorted(results, key=lambda e: e.reuse_count, reverse=True)[:top_n]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "built_at": self.built_at,
            "total_patterns": self.total_patterns,
            "entries": [
                {
                    "task_kind": e.task_kind,
                    "target_file_suffix": e.target_file_suffix,
                    "old_string_prefix": e.old_string_prefix,
                    "new_string_prefix": e.new_string_prefix,
                    "reuse_count": e.reuse_count,
                    "recorded_at": e.recorded_at,
                }
                for e in self.entries
            ],
        }


def build_repo_pattern_library(
    memory_store: LocalMemoryStore,
    *,
    top_n: int = 50,
) -> RepoPatternLibrary:
    """Build a RepoPatternLibrary from accumulated SuccessPattern records."""
    records = memory_store.query_successes(limit=10_000)

    merged: dict[tuple, dict] = {}
    for r in records:
        key = (r.task_kind, r.target_file_suffix, r.old_string_prefix)
        if key in merged:
            merged[key]["reuse_count"] += r.reuse_count
            merged[key]["recorded_at"] = max(merged[key]["recorded_at"], r.recorded_at)
        else:
            merged[key] = {
                "task_kind": r.task_kind,
                "target_file_suffix": r.target_file_suffix,
                "old_string_prefix": r.old_string_prefix,
                "new_string_prefix": r.new_string_prefix,
                "reuse_count": r.reuse_count,
                "recorded_at": r.recorded_at,
            }

    sorted_entries = sorted(merged.values(), key=lambda e: e["reuse_count"], reverse=True)[:top_n]
    entries = [PatternEntry(**e) for e in sorted_entries]

    library = RepoPatternLibrary(
        entries=entries,
        built_at=_iso_now(),
        total_patterns=len(entries),
    )
    return library


def save_repo_pattern_library(
    library: RepoPatternLibrary,
    *,
    artifact_dir: Optional[Path] = None,
    dry_run: bool = False,
) -> Optional[str]:
    """Save library as JSON artifact. Returns path or None on dry_run."""
    if dry_run:
        return None

    out_dir = Path(artifact_dir) if artifact_dir else _DEFAULT_ARTIFACT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    artifact_file = out_dir / "patterns.json"
    artifact_file.write_text(
        json.dumps(library.to_dict(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return str(artifact_file)


__all__ = [
    "PatternEntry",
    "RepoPatternLibrary",
    "build_repo_pattern_library",
    "save_repo_pattern_library",
]
