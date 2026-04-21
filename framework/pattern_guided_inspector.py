"""PatternGuidedInspector — queries RepoPatternLibrary for pre-task file and string hints.

Inspection gate output:
  RepoPatternLibrary.query sig: (self, *, task_kind=None, target_file_suffix=None, top_n=10) -> list[PatternEntry]
  PatternEntry fields: task_kind, target_file_suffix, old_string_prefix, new_string_prefix, reuse_count, recorded_at
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from framework.repo_pattern_store import PatternEntry, RepoPatternLibrary

assert callable(RepoPatternLibrary), "INTERFACE MISMATCH: RepoPatternLibrary not callable"
assert "reuse_count" in PatternEntry.__dataclass_fields__, "INTERFACE MISMATCH: PatternEntry.reuse_count missing"


@dataclass(frozen=True)
class InspectHint:
    target_file_suffix: str
    old_string_prefix: str
    confidence: float
    source: str


class PatternGuidedInspector:
    """Returns ranked inspect hints from RepoPatternLibrary for a task kind."""

    def __init__(self, pattern_library: RepoPatternLibrary) -> None:
        self._library = pattern_library

    def hints_for(self, task_kind: str, top_n: int = 5) -> list:
        entries = self._library.query(task_kind=task_kind, top_n=top_n)
        if not entries:
            return []
        max_reuse = max(e.reuse_count for e in entries) or 1
        hints = []
        for e in entries:
            confidence = e.reuse_count / max_reuse
            hints.append(InspectHint(
                target_file_suffix=e.target_file_suffix,
                old_string_prefix=e.old_string_prefix,
                confidence=confidence,
                source="pattern_library",
            ))
        hints.sort(key=lambda h: h.confidence, reverse=True)
        return hints[:top_n]

    def hint_snippet(self, task_kind: str, top_n: int = 5) -> str:
        hints = self.hints_for(task_kind, top_n=top_n)
        if not hints:
            return f"[no pattern hints for task_kind={task_kind!r}]"
        lines = [f"Pattern hints for {task_kind!r}:"]
        for h in hints:
            lines.append(
                f"  file_suffix={h.target_file_suffix!r} "
                f"old_prefix={h.old_string_prefix!r} "
                f"confidence={h.confidence:.2f}"
            )
        return "\n".join(lines)


__all__ = ["InspectHint", "PatternGuidedInspector"]
