"""LACE1-P9-LOCAL-BENCHMARK-TASK-PACK-SEAM-1: 12-task synthetic local autonomy benchmark pack."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List

from framework.devloop_benchmark import DevloopTask, SYNTHETIC_TASK_FAMILY

assert len(SYNTHETIC_TASK_FAMILY) >= 2, "INTERFACE MISMATCH: SYNTHETIC_TASK_FAMILY too small"


@dataclass(frozen=True)
class LocalAutonomyTask:
    task_id: str
    task_kind: str
    description: str
    file_name: str
    initial_content: str
    old_string: str
    new_string: str
    expected_content: str
    loe_points: int
    acceptance_grep: str


def _mk(
    task_id: str,
    task_kind: str,
    description: str,
    file_name: str,
    initial_content: str,
    old_string: str,
    new_string: str,
    loe_points: int,
    acceptance_grep: str,
) -> LocalAutonomyTask:
    expected_content = initial_content.replace(old_string, new_string, 1)
    return LocalAutonomyTask(
        task_id=task_id,
        task_kind=task_kind,
        description=description,
        file_name=file_name,
        initial_content=initial_content,
        old_string=old_string,
        new_string=new_string,
        expected_content=expected_content,
        loe_points=loe_points,
        acceptance_grep=acceptance_grep,
    )


LACE1_TASK_PACK: tuple = (
    # --- text_replacement × 3 ---
    _mk(
        "LACE1-TR-01", "text_replacement",
        "Replace APP_VERSION constant from 1.0.0 to 1.1.0",
        "version_marker.py",
        'APP_VERSION = "1.0.0"\n',
        'APP_VERSION = "1.0.0"',
        'APP_VERSION = "1.1.0"',
        1,
        r'APP_VERSION = "1\.1\.0"',
    ),
    _mk(
        "LACE1-TR-02", "text_replacement",
        "Replace TIMEOUT_SECONDS from 10 to 30",
        "retry_config.py",
        "TIMEOUT_SECONDS = 10\n",
        "TIMEOUT_SECONDS = 10",
        "TIMEOUT_SECONDS = 30",
        1,
        r"TIMEOUT_SECONDS = 30",
    ),
    _mk(
        "LACE1-TR-03", "text_replacement",
        "Replace LOG_LEVEL from DEBUG to INFO",
        "logging_config.py",
        'LOG_LEVEL = "DEBUG"\n',
        'LOG_LEVEL = "DEBUG"',
        'LOG_LEVEL = "INFO"',
        1,
        r'LOG_LEVEL = "INFO"',
    ),
    # --- insert_block × 3 ---
    _mk(
        "LACE1-IB-01", "insert_block",
        "Insert truncate helper after capitalize function",
        "string_utils.py",
        "def capitalize(s):\n    return s.upper()\n",
        "def capitalize(s):\n    return s.upper()\n",
        "def capitalize(s):\n    return s.upper()\n\ndef truncate(s, n):\n    return s[:n]\n",
        2,
        r"def truncate",
    ),
    _mk(
        "LACE1-IB-02", "insert_block",
        "Insert docstring into parse_line function",
        "parser.py",
        "def parse_line(line):\n    return line.strip()\n",
        "def parse_line(line):\n    return line.strip()\n",
        'def parse_line(line):\n    """Strip and return the line."""\n    return line.strip()\n',
        2,
        r"Strip and return",
    ),
    _mk(
        "LACE1-IB-03", "insert_block",
        "Insert MIN_SIZE and DEFAULT_SIZE constants after MAX_SIZE",
        "defaults.py",
        "MAX_SIZE = 100\n",
        "MAX_SIZE = 100\n",
        "MAX_SIZE = 100\nMIN_SIZE = 1\nDEFAULT_SIZE = 10\n",
        2,
        r"MIN_SIZE",
    ),
    # --- add_guard × 2 ---
    _mk(
        "LACE1-AG-01", "add_guard",
        "Add None guard clause to validate function",
        "validator.py",
        "def validate(data):\n    return bool(data)\n",
        "def validate(data):\n    return bool(data)\n",
        "def validate(data):\n    if data is None:\n        return False\n    return bool(data)\n",
        2,
        r"if data is None",
    ),
    _mk(
        "LACE1-AG-02", "add_guard",
        "Add empty string guard to format_name function",
        "formatter.py",
        "def format_name(name):\n    return name.title()\n",
        "def format_name(name):\n    return name.title()\n",
        'def format_name(name):\n    if not name:\n        return ""\n    return name.title()\n',
        2,
        r"if not name",
    ),
    # --- add_test × 2 ---
    _mk(
        "LACE1-AT-01", "add_test",
        "Add test_decrement test function after test_increment",
        "test_counter.py",
        "def test_increment():\n    assert 1 + 1 == 2\n",
        "def test_increment():\n    assert 1 + 1 == 2\n",
        "def test_increment():\n    assert 1 + 1 == 2\n\ndef test_decrement():\n    assert 2 - 1 == 1\n",
        2,
        r"def test_decrement",
    ),
    _mk(
        "LACE1-AT-02", "add_test",
        "Add second assertion to test_upper for world.upper()",
        "test_string_ops.py",
        'def test_upper():\n    assert "hello".upper() == "HELLO"\n',
        'def test_upper():\n    assert "hello".upper() == "HELLO"\n',
        'def test_upper():\n    assert "hello".upper() == "HELLO"\n    assert "world".upper() == "WORLD"\n',
        2,
        r'"world"\.upper',
    ),
    # --- add_field × 2 ---
    _mk(
        "LACE1-AF-01", "add_field",
        "Add status field to Record dataclass",
        "record_schema.py",
        "from dataclasses import dataclass\n\n@dataclass\nclass Record:\n    record_id: str\n    value: str\n",
        "    value: str\n",
        '    value: str\n    status: str = "active"\n',
        2,
        r"status: str",
    ),
    _mk(
        "LACE1-AF-02", "add_field",
        "Add verbose field to Config dataclass",
        "config_schema.py",
        "from dataclasses import dataclass\n\n@dataclass\nclass Config:\n    name: str\n    debug: bool = False\n",
        "    debug: bool = False\n",
        "    debug: bool = False\n    verbose: bool = False\n",
        2,
        r"verbose: bool",
    ),
)


def load_benchmark_pack(path: Path) -> List[LocalAutonomyTask]:
    """Load a benchmark pack from a JSON file previously emitted by emit_benchmark_pack."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return [LocalAutonomyTask(**t) for t in data["tasks"]]


def emit_benchmark_pack(tasks: tuple, artifact_dir: Path) -> str:
    artifact_dir = Path(artifact_dir)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    out_path = artifact_dir / "benchmark_pack.json"
    out_path.write_text(
        json.dumps(
            {
                "pack_id": "LACE1-BENCHMARK-PACK",
                "task_count": len(tasks),
                "kind_summary": _kind_summary(tasks),
                "tasks": [asdict(t) for t in tasks],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return str(out_path)


def _kind_summary(tasks: tuple) -> dict:
    counts: dict = {}
    for t in tasks:
        counts[t.task_kind] = counts.get(t.task_kind, 0) + 1
    return counts


def validate_acceptance_greps(tasks: tuple) -> List[str]:
    """Return list of task_ids with non-compilable acceptance_grep patterns."""
    bad = []
    for t in tasks:
        try:
            re.compile(t.acceptance_grep)
        except re.error:
            bad.append(t.task_id)
    return bad


__all__ = [
    "LocalAutonomyTask",
    "LACE1_TASK_PACK",
    "load_benchmark_pack",
    "emit_benchmark_pack",
    "validate_acceptance_greps",
]
