"""Offline regression for framework.runtime_workspace_contract."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from framework.runtime_workspace_contract import (
    assert_read_only_source,
    build_workspace,
)


class RuntimeWorkspaceContractTest(unittest.TestCase):
    def test_build_workspace_deterministic_layout(self) -> None:
        with tempfile.TemporaryDirectory() as src, tempfile.TemporaryDirectory() as base:
            ws = build_workspace(
                source_root=Path(src),
                base_root=Path(base),
                run_id="r1",
                session_id="s1",
            )
            self.assertEqual(ws.run_id, "r1")
            self.assertEqual(ws.session_id, "s1")
            self.assertEqual(
                ws.scratch_root,
                Path(base).resolve() / "scratch" / "s1" / "r1",
            )
            self.assertEqual(
                ws.artifact_root,
                Path(base).resolve() / "artifacts" / "s1" / "r1",
            )

    def test_ensure_materialized_creates_directories(self) -> None:
        with tempfile.TemporaryDirectory() as src, tempfile.TemporaryDirectory() as base:
            ws = build_workspace(
                source_root=Path(src),
                base_root=Path(base),
                run_id="r1",
                session_id="s1",
            )
            self.assertFalse(ws.scratch_root.exists())
            self.assertFalse(ws.artifact_root.exists())
            ws.ensure_materialized()
            self.assertTrue(ws.scratch_root.is_dir())
            self.assertTrue(ws.artifact_root.is_dir())

    def test_empty_run_id_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as src, tempfile.TemporaryDirectory() as base:
            with self.assertRaises(ValueError):
                build_workspace(
                    source_root=Path(src),
                    base_root=Path(base),
                    run_id="",
                    session_id="s1",
                )

    def test_empty_session_id_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as src, tempfile.TemporaryDirectory() as base:
            with self.assertRaises(ValueError):
                build_workspace(
                    source_root=Path(src),
                    base_root=Path(base),
                    run_id="r1",
                    session_id="",
                )

    def test_assert_read_only_source_blocks_source_writes(self) -> None:
        with tempfile.TemporaryDirectory() as src, tempfile.TemporaryDirectory() as base:
            ws = build_workspace(
                source_root=Path(src),
                base_root=Path(base),
                run_id="r1",
                session_id="s1",
            )
            scratch_path = ws.scratch_root / "ok.txt"
            artifact_path = ws.artifact_root / "ok.txt"
            assert_read_only_source(ws, scratch_path)  # ok
            assert_read_only_source(ws, artifact_path)  # ok
            with self.assertRaises(PermissionError):
                assert_read_only_source(ws, Path(src) / "forbidden.txt")

    def test_to_dict_has_string_paths(self) -> None:
        with tempfile.TemporaryDirectory() as src, tempfile.TemporaryDirectory() as base:
            ws = build_workspace(
                source_root=Path(src),
                base_root=Path(base),
                run_id="r1",
                session_id="s1",
            )
            d = ws.to_dict()
            self.assertEqual(d["run_id"], "r1")
            self.assertEqual(d["session_id"], "s1")
            self.assertIsInstance(d["source_root"], str)
            self.assertIsInstance(d["scratch_root"], str)
            self.assertIsInstance(d["artifact_root"], str)


if __name__ == "__main__":
    unittest.main()
