#!/usr/bin/env python3
"""
Regression test: corrupt file detection.
No Ollama or aider required — purely local.
Verifies that the validation layer catches corrupt Python/shell syntax
before any changes are committed.
"""
import ast
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent.parent


def check_python_syntax(path: Path) -> tuple[bool, str]:
    """Return (ok, error_message) for a Python file."""
    try:
        # read_bytes to catch invalid encoding before ast.parse
        raw = path.read_bytes()
        try:
            source = raw.decode("utf-8")
        except UnicodeDecodeError as e:
            return False, f"UnicodeDecodeError: {e}"
        ast.parse(source)
        return True, ""
    except SyntaxError as e:
        return False, f"SyntaxError line {e.lineno}: {e.msg}"
    except ValueError as e:
        # ast.parse raises ValueError for null bytes
        return False, f"ValueError: {e}"


def check_shell_syntax(path: Path) -> tuple[bool, str]:
    """Return (ok, error_message) for a shell script using shellcheck."""
    result = subprocess.run(
        ["bash", "-n", str(path)],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        return False, result.stderr.strip()
    return True, ""


class TestPythonCorruptionDetection:
    """Verify Python syntax errors are caught before commit."""

    def test_valid_python_passes(self, tmp_path):
        """A syntactically valid Python file must pass."""
        f = tmp_path / "valid.py"
        f.write_text("def hello():\n    return 42\n")
        ok, err = check_python_syntax(f)
        assert ok, f"Valid Python flagged as corrupt: {err}"

    def test_syntax_error_detected(self, tmp_path):
        """A Python file with a syntax error must be detected."""
        f = tmp_path / "corrupt.py"
        f.write_text("def broken(:\n    pass\n")
        ok, err = check_python_syntax(f)
        assert not ok, "Corrupt Python was not detected"
        assert err, "No error message returned for corrupt file"
        print(f"\nDetected: {err}")

    def test_truncated_file_detected(self, tmp_path):
        """A truncated file (cut mid-function) must be detected."""
        f = tmp_path / "truncated.py"
        f.write_text("class MyClass:\n    def method(self")  # no closing
        ok, err = check_python_syntax(f)
        assert not ok, "Truncated Python was not detected"
        print(f"\nDetected truncation: {err}")

    def test_null_bytes_detected(self, tmp_path):
        """A file with embedded null bytes must be detected."""
        f = tmp_path / "null_bytes.py"
        f.write_bytes(b"def hello():\n    return \x00\n")
        ok, err = check_python_syntax(f)
        assert not ok, "Null-byte corruption was not detected"
        print(f"\nDetected null bytes: {err}")

    def test_unicode_corruption_detected(self, tmp_path):
        """A file with invalid UTF-8 sequences must be detected."""
        f = tmp_path / "bad_unicode.py"
        f.write_bytes(b"def hello():\n    x = '\xff\xfe'\n")
        ok, err = check_python_syntax(f)
        assert not ok, "Unicode corruption was not detected"
        print(f"\nDetected unicode corruption: {err}")

    def test_all_existing_py_files_are_valid(self):
        """Every checked-in .py file in the repo must parse cleanly."""
        repo_py_files = list(REPO_ROOT.glob("**/*.py"))
        # Exclude vendored/archive directories
        exclude = {".archive", ".git", "__pycache__", ".venv", "venv", "env"}
        py_files = [
            f for f in repo_py_files
            if not any(part in exclude for part in f.parts)
        ]

        corrupted = []
        for f in py_files:
            ok, err = check_python_syntax(f)
            if not ok:
                corrupted.append((f.relative_to(REPO_ROOT), err))

        if corrupted:
            details = "\n".join(f"  {path}: {err}" for path, err in corrupted)
            pytest.fail(f"{len(corrupted)} corrupt Python files:\n{details}")

        print(f"\n✓ All {len(py_files)} Python files parse cleanly")


class TestShellCorruptionDetection:
    """Verify shell script syntax errors are caught before commit."""

    def test_valid_shell_passes(self, tmp_path):
        """A valid shell script must pass."""
        f = tmp_path / "valid.sh"
        f.write_text("#!/bin/bash\necho hello\n")
        ok, err = check_shell_syntax(f)
        assert ok, f"Valid shell flagged as corrupt: {err}"

    def test_unclosed_function_detected(self, tmp_path):
        """Unclosed function body must be detected."""
        f = tmp_path / "bad.sh"
        # bash -n catches unclosed do/done pairs
        f.write_text("#!/bin/bash\nfor x in a b c; do\necho $x\n")
        ok, err = check_shell_syntax(f)
        assert not ok, "Shell syntax error (unclosed for loop) was not detected"
        print(f"\nDetected: {err}")

    def test_unclosed_string_detected(self, tmp_path):
        """Unclosed string must be detected."""
        f = tmp_path / "bad2.sh"
        f.write_text('#!/bin/bash\necho "unclosed string\n')
        ok, err = check_shell_syntax(f)
        assert not ok, "Unclosed string was not detected"
        print(f"\nDetected: {err}")


class TestRoadmapCorruptionDetection:
    """Verify roadmap markdown is loadable and well-formed."""

    def test_all_roadmap_items_parse(self):
        """Every RM-*.md file must load without errors."""
        import sys
        sys.path.insert(0, str(REPO_ROOT))
        from bin.roadmap_parser import parse_roadmap_directory

        items_dir = REPO_ROOT / "docs" / "roadmap" / "ITEMS"
        try:
            items = parse_roadmap_directory(items_dir)
        except Exception as e:
            pytest.fail(f"Roadmap parser crashed: {e}")

        assert len(items) > 0, "Parser loaded 0 items — directory may be empty"

        # Every item must have required fields
        required_fields = ["id", "title", "status"]
        malformed = []
        for item in items:
            for field in required_fields:
                if not getattr(item, field, None):
                    malformed.append((item.id, f"missing {field}"))

        if malformed:
            details = "\n".join(f"  {item_id}: {err}" for item_id, err in malformed)
            pytest.fail(f"{len(malformed)} malformed roadmap items:\n{details}")

        print(f"\n✓ All {len(items)} roadmap items load without errors")

    def test_no_circular_dependencies(self):
        """Circular dependencies must be 0 — they block executor progress."""
        import sys
        sys.path.insert(0, str(REPO_ROOT))
        from bin.roadmap_parser import (
            parse_roadmap_directory, infer_dependencies, detect_cycles
        )

        items = parse_roadmap_directory(REPO_ROOT / "docs" / "roadmap" / "ITEMS")
        infer_dependencies(items)
        cycles = detect_cycles(items)

        assert len(cycles) == 0, (
            f"{len(cycles)} circular dependency cycles detected.\n"
            "Run: python3 bin/break_dependency_cycles.py\n"
            "Cycles:\n" + "\n".join("  " + " → ".join(c) for c in cycles[:5])
        )
        print(f"\n✓ 0 circular dependencies")

    def test_glob_loads_only_md_files(self):
        """Roadmap parser must ignore .yaml/.json files — only RM-*.md loads."""
        items_dir = REPO_ROOT / "docs" / "roadmap" / "ITEMS"
        non_md = list(items_dir.glob("RM-*.yaml")) + list(items_dir.glob("RM-*.json"))
        assert not non_md, (
            f"Found {len(non_md)} non-.md roadmap files that parser will ignore:\n"
            + "\n".join(f"  {f.name}" for f in non_md)
        )
        print(f"\n✓ All roadmap files use .md extension")
