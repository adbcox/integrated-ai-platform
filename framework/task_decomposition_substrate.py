"""LACE1-P3-TASK-DECOMP-SUBSTRATE-SEAM-1: deterministic task decomposition producing DecomposedTaskBundle."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from framework.evidence_backed_task_expander import EvidenceBackedTaskExpander

assert callable(EvidenceBackedTaskExpander), "INTERFACE MISMATCH: EvidenceBackedTaskExpander not callable"


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")


_KIND_KEYWORDS = {
    "add_test": ("test", "assert", "pytest", "unittest"),
    "add_guard": ("guard", "precondition", "validate", "check", "raise if", "assert if"),
    "add_field": ("field", "attribute", "property", "dataclass field", "add field"),
    "replace_text": ("replace", "rename", "update constant", "change value", "bump version"),
    "insert_block": (),  # fallback
}


def _classify_kind(description: str) -> str:
    desc_lower = description.lower()
    for kind, keywords in _KIND_KEYWORDS.items():
        if kind == "insert_block":
            continue
        for kw in keywords:
            if kw in desc_lower:
                return kind
    return "insert_block"


@dataclass(frozen=True)
class SubTask:
    subtask_id: str
    kind: str           # "replace_text"|"insert_block"|"add_guard"|"add_test"|"add_field"
    target_file: str
    description: str
    scope_hint: str
    acceptance_signal: str


@dataclass
class DecomposedTaskBundle:
    bundle_id: str
    source_description: str
    subtasks: List[SubTask]
    estimated_total_loe: int
    decomposed_at: str
    artifact_path: Optional[str] = None


class TaskDecompositionSubstrate:
    """Deterministic keyword-driven task decomposer."""

    def decompose(
        self,
        description: str,
        target_files: List[str],
        *,
        bundle_id: Optional[str] = None,
    ) -> DecomposedTaskBundle:
        if bundle_id is None:
            bundle_id = f"BUNDLE-{_ts()}"

        kind = _classify_kind(description)
        subtasks = []
        for i, target_file in enumerate(target_files):
            subtask_id = f"{bundle_id}-ST{i+1:02d}"
            file_kind = _classify_kind(description)
            acceptance_signal = f"grep -q '{kind}' {target_file}"
            subtasks.append(
                SubTask(
                    subtask_id=subtask_id,
                    kind=file_kind,
                    target_file=target_file,
                    description=description,
                    scope_hint=f"max 20 lines in {Path(target_file).name}",
                    acceptance_signal=acceptance_signal,
                )
            )

        return DecomposedTaskBundle(
            bundle_id=bundle_id,
            source_description=description,
            subtasks=subtasks,
            estimated_total_loe=len(subtasks),
            decomposed_at=_iso_now(),
        )

    def emit(self, bundle: DecomposedTaskBundle, artifact_dir: Path) -> str:
        artifact_dir = Path(artifact_dir)
        artifact_dir.mkdir(parents=True, exist_ok=True)
        out_path = artifact_dir / f"{bundle.bundle_id}.json"
        out_path.write_text(
            json.dumps(
                {
                    "bundle_id": bundle.bundle_id,
                    "source_description": bundle.source_description,
                    "subtasks": [asdict(s) for s in bundle.subtasks],
                    "estimated_total_loe": bundle.estimated_total_loe,
                    "decomposed_at": bundle.decomposed_at,
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        bundle.artifact_path = str(out_path)
        return str(out_path)


__all__ = ["SubTask", "DecomposedTaskBundle", "TaskDecompositionSubstrate"]
