"""Age-based and reuse-based eviction for RepoPatternLibrary entries."""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from framework.repo_pattern_store import PatternEntry, RepoPatternLibrary

# -- import-time assertions --
assert "entries" in RepoPatternLibrary.__dataclass_fields__, \
    "INTERFACE MISMATCH: RepoPatternLibrary.entries"
assert "recorded_at" in PatternEntry.__dataclass_fields__, \
    "INTERFACE MISMATCH: PatternEntry.recorded_at"
assert "reuse_count" in PatternEntry.__dataclass_fields__, \
    "INTERFACE MISMATCH: PatternEntry.reuse_count"
assert callable(getattr(RepoPatternLibrary, "to_dict", None)), \
    "INTERFACE MISMATCH: RepoPatternLibrary.to_dict"


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _parse_dt(ts: str) -> Optional[datetime]:
    try:
        return datetime.fromisoformat(ts)
    except (ValueError, TypeError):
        return None


@dataclass(frozen=True)
class PatternEvictionResult:
    total_before: int
    evicted_by_age: int
    evicted_by_reuse: int
    total_after: int
    evicted_at: str


def evict_stale_patterns(
    library: RepoPatternLibrary,
    *,
    max_age_days: int = 30,
    min_reuse_count: int = 1,
) -> tuple:
    now = datetime.now(timezone.utc)
    evicted_by_age = 0
    evicted_by_reuse = 0
    kept: list[PatternEntry] = []

    for entry in library.entries:
        dt = _parse_dt(entry.recorded_at)
        age_ok = True
        if dt is not None:
            # make dt timezone-aware if naive
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            age_days = (now - dt).days
            if age_days > max_age_days:
                evicted_by_age += 1
                age_ok = False

        if not age_ok:
            continue

        if entry.reuse_count < min_reuse_count:
            evicted_by_reuse += 1
            continue

        kept.append(entry)

    new_library = RepoPatternLibrary(
        entries=kept,
        built_at=library.built_at,
        total_patterns=len(kept),
    )
    eviction_result = PatternEvictionResult(
        total_before=len(library.entries),
        evicted_by_age=evicted_by_age,
        evicted_by_reuse=evicted_by_reuse,
        total_after=len(kept),
        evicted_at=_iso_now(),
    )
    return new_library, eviction_result


def persist_eviction(library: RepoPatternLibrary, artifact_dir: Path) -> str:
    artifact_dir = Path(artifact_dir)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    out_path = artifact_dir / "pattern_library_post_eviction.json"
    out_path.write_text(json.dumps(library.to_dict(), indent=2), encoding="utf-8")
    return str(out_path)


__all__ = ["PatternEvictionResult", "evict_stale_patterns", "persist_eviction"]
