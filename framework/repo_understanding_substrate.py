"""LACE1-P2-REPO-UNDERSTANDING-SUBSTRATE-SEAM-1: typed repo understanding surface wrapping RepomapGenerator."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from framework.codebase_repomap import RepomapGenerator, RepomapEntry

assert callable(RepomapGenerator), "INTERFACE MISMATCH: RepomapGenerator not callable"
assert hasattr(RepomapGenerator, "scan_repository"), "INTERFACE MISMATCH: RepomapGenerator.scan_repository missing"
assert "path" in RepomapEntry.__dataclass_fields__, "INTERFACE MISMATCH: RepomapEntry.path missing"
assert "symbols" in RepomapEntry.__dataclass_fields__, "INTERFACE MISMATCH: RepomapEntry.symbols missing"


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass(frozen=True)
class RepoUnderstandingSummary:
    summary_id: str
    total_files_scanned: int
    total_symbols: int
    top_files_by_symbol_count: List[dict]   # [{path, symbol_count}] top 10
    framework_file_count: int
    bin_file_count: int
    test_file_count: int
    generated_at: str
    artifact_path: Optional[str] = None


class RepoUnderstandingSubstrate:
    """Wraps RepomapGenerator to produce a typed RepoUnderstandingSummary."""

    def __init__(self, repo_root: Path) -> None:
        self._repo_root = Path(repo_root)
        self._generator = RepomapGenerator(self._repo_root)

    def scan(self, max_files: int = 500) -> RepoUnderstandingSummary:
        try:
            entries: dict[str, RepomapEntry] = self._generator.scan_repository(
                max_files=max_files
            )
        except Exception:
            return RepoUnderstandingSummary(
                summary_id="empty",
                total_files_scanned=0,
                total_symbols=0,
                top_files_by_symbol_count=[],
                framework_file_count=0,
                bin_file_count=0,
                test_file_count=0,
                generated_at=_iso_now(),
            )

        total_files = len(entries)
        total_symbols = sum(len(e.symbols) if e.symbols else 0 for e in entries.values())

        sorted_by_symbols = sorted(
            entries.values(),
            key=lambda e: len(e.symbols) if e.symbols else 0,
            reverse=True,
        )
        top_files = [
            {"path": e.path, "symbol_count": len(e.symbols) if e.symbols else 0}
            for e in sorted_by_symbols[:10]
        ]

        framework_count = sum(1 for p in entries if p.startswith("framework/") or "/framework/" in p)
        bin_count = sum(1 for p in entries if p.startswith("bin/") or "/bin/" in p)
        test_count = sum(1 for p in entries if p.startswith("tests/") or "/tests/" in p)

        return RepoUnderstandingSummary(
            summary_id=f"RUS-{_iso_now().replace(':','')}",
            total_files_scanned=total_files,
            total_symbols=total_symbols,
            top_files_by_symbol_count=top_files,
            framework_file_count=framework_count,
            bin_file_count=bin_count,
            test_file_count=test_count,
            generated_at=_iso_now(),
        )

    def emit(self, summary: RepoUnderstandingSummary, artifact_dir: Path) -> str:
        artifact_dir = Path(artifact_dir)
        artifact_dir.mkdir(parents=True, exist_ok=True)
        out_path = artifact_dir / "repo_understanding_baseline.json"
        out_path.write_text(
            json.dumps(
                {
                    "summary_id": summary.summary_id,
                    "total_files_scanned": summary.total_files_scanned,
                    "total_symbols": summary.total_symbols,
                    "top_files_by_symbol_count": summary.top_files_by_symbol_count,
                    "framework_file_count": summary.framework_file_count,
                    "bin_file_count": summary.bin_file_count,
                    "test_file_count": summary.test_file_count,
                    "generated_at": summary.generated_at,
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        return str(out_path)


__all__ = ["RepoUnderstandingSubstrate", "RepoUnderstandingSummary"]
