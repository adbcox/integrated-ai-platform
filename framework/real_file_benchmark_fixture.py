"""LACE2-P8-REAL-FILE-FIXTURE-SEAM-1: tmp-file fixture setup/teardown for RealFileTask execution."""
from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from framework.real_file_benchmark_pack import RealFileTask

assert "initial_content" in RealFileTask.__dataclass_fields__, "INTERFACE MISMATCH: RealFileTask.initial_content"
assert "old_string" in RealFileTask.__dataclass_fields__, "INTERFACE MISMATCH: RealFileTask.old_string"
assert "new_string" in RealFileTask.__dataclass_fields__, "INTERFACE MISMATCH: RealFileTask.new_string"
assert "expected_content" in RealFileTask.__dataclass_fields__, "INTERFACE MISMATCH: RealFileTask.expected_content"


@dataclass
class FixtureResult:
    task_id: str
    fixture_path: Path
    initial_content: str
    expected_content: str
    setup_ok: bool
    teardown_ok: Optional[bool] = None


class RealFileBenchmarkFixture:
    """Sets up a tmp file with `initial_content`, tears it down after use."""

    def setup(self, task: RealFileTask, tmp_dir: Path) -> FixtureResult:
        tmp_dir = Path(tmp_dir)
        tmp_dir.mkdir(parents=True, exist_ok=True)
        fixture_path = tmp_dir / f"{task.task_id}.txt"
        fixture_path.write_text(task.initial_content, encoding="utf-8")
        readback = fixture_path.read_text(encoding="utf-8")
        setup_ok = readback == task.initial_content
        return FixtureResult(
            task_id=task.task_id,
            fixture_path=fixture_path,
            initial_content=task.initial_content,
            expected_content=task.expected_content,
            setup_ok=setup_ok,
        )

    def teardown(self, result: FixtureResult) -> bool:
        try:
            if result.fixture_path.exists():
                result.fixture_path.unlink()
            result.teardown_ok = True
            return True
        except OSError:
            result.teardown_ok = False
            return False


__all__ = ["FixtureResult", "RealFileBenchmarkFixture"]
