"""Offline tests for framework/developer_assistance_service.py.

All tests use tempfile.TemporaryDirectory and monkey-patching to avoid
touching real runtime/ files.
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

import framework.developer_assistance_service as _svc


def _write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")


def _minimal_manifest() -> dict:
    return {
        "schema_version": 1,
        "generated_at": "2026-04-20T00:00:00Z",
        "subsystem": "developer_assistance",
        "phase": 1,
        "status": "active",
        "ollama_endpoint": "http://localhost:11434",
        "model_profile": "fast",
        "model_id": "qwen2.5-coder:14b",
        "tool_registry_ref": "runtime/developer_assistance_tool_registry.json",
        "gating_rules": {"patch_requires_queue": True, "auto_commit": False},
    }


def _minimal_registry(tools=None) -> dict:
    if tools is None:
        tools = [
            {"name": "read_file", "category": "file_read", "risk_level": "low",
             "access_mode": "always_allowed", "enabled": True, "description": "d", "manifest_field": "t.r"},
            {"name": "propose_patch", "category": "patch_proposal", "risk_level": "medium",
             "access_mode": "queue_required", "enabled": False, "description": "d", "manifest_field": "t.p"},
        ]
    return {
        "schema_version": 1,
        "generated_at": "2026-04-20T00:00:00Z",
        "subsystem": "developer_assistance",
        "tool_count": len(tools),
        "tools": tools,
    }


class ManifestLoadTest(unittest.TestCase):
    def test_load_manifest_returns_dict(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "manifest.json"
            _write_json(path, _minimal_manifest())
            with mock.patch.object(_svc, "MANIFEST_PATH", path):
                result = _svc.load_manifest()
            self.assertIsInstance(result, dict)

    def test_load_manifest_raises_on_missing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "nonexistent.json"
            with mock.patch.object(_svc, "MANIFEST_PATH", path):
                with self.assertRaises(FileNotFoundError):
                    _svc.load_manifest()

    def test_manifest_schema_version_is_1(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "manifest.json"
            _write_json(path, _minimal_manifest())
            with mock.patch.object(_svc, "MANIFEST_PATH", path):
                result = _svc.load_manifest()
            self.assertEqual(result["schema_version"], 1)


class ToolRegistryLoadTest(unittest.TestCase):
    def test_load_tool_registry_returns_dict(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "registry.json"
            _write_json(path, _minimal_registry())
            with mock.patch.object(_svc, "TOOL_REGISTRY_PATH", path):
                result = _svc.load_tool_registry()
            self.assertIsInstance(result, dict)

    def test_tool_registry_has_tools_key(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "registry.json"
            _write_json(path, _minimal_registry())
            with mock.patch.object(_svc, "TOOL_REGISTRY_PATH", path):
                result = _svc.load_tool_registry()
            self.assertIn("tools", result)
            self.assertIsInstance(result["tools"], list)

    def test_tool_count_matches_tools_list_length(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "registry.json"
            reg = _minimal_registry()
            _write_json(path, reg)
            with mock.patch.object(_svc, "TOOL_REGISTRY_PATH", path):
                result = _svc.load_tool_registry()
            self.assertEqual(result["tool_count"], len(result["tools"]))


class GetStatusTest(unittest.TestCase):
    def _patched(self, manifest_path, registry_path,
                 queue_path=None, sessions_path=None):
        patches = [
            mock.patch.object(_svc, "MANIFEST_PATH", manifest_path),
            mock.patch.object(_svc, "TOOL_REGISTRY_PATH", registry_path),
        ]
        if queue_path is not None:
            patches.append(mock.patch.object(_svc, "REVIEW_QUEUE_PATH", queue_path))
        if sessions_path is not None:
            patches.append(mock.patch.object(_svc, "SESSIONS_PATH", sessions_path))
        return patches

    def test_get_status_never_raises(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            mp = Path(tmpdir) / "m.json"
            rp = Path(tmpdir) / "r.json"
            with mock.patch.object(_svc, "MANIFEST_PATH", mp), \
                 mock.patch.object(_svc, "TOOL_REGISTRY_PATH", rp):
                result = _svc.get_status()
            self.assertIsInstance(result, dict)

    def test_status_has_all_required_keys(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            mp = Path(tmpdir) / "m.json"
            rp = Path(tmpdir) / "r.json"
            with mock.patch.object(_svc, "MANIFEST_PATH", mp), \
                 mock.patch.object(_svc, "TOOL_REGISTRY_PATH", rp):
                result = _svc.get_status()
            required = [
                "subsystem", "phase", "status", "model_id", "ollama_endpoint",
                "tool_count", "open_review_count", "session_count",
                "manifest_present", "tool_registry_present",
            ]
            for key in required:
                self.assertIn(key, result, msg=f"missing key {key!r}")

    def test_status_manifest_present_true_when_file_exists(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            mp = Path(tmpdir) / "m.json"
            rp = Path(tmpdir) / "r.json"
            _write_json(mp, _minimal_manifest())
            with mock.patch.object(_svc, "MANIFEST_PATH", mp), \
                 mock.patch.object(_svc, "TOOL_REGISTRY_PATH", rp):
                result = _svc.get_status()
            self.assertTrue(result["manifest_present"])

    def test_status_manifest_present_false_when_absent(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            mp = Path(tmpdir) / "missing.json"
            rp = Path(tmpdir) / "r.json"
            with mock.patch.object(_svc, "MANIFEST_PATH", mp), \
                 mock.patch.object(_svc, "TOOL_REGISTRY_PATH", rp):
                result = _svc.get_status()
            self.assertFalse(result["manifest_present"])

    def test_status_open_review_count_zero_when_no_queue(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            mp = Path(tmpdir) / "m.json"
            rp = Path(tmpdir) / "r.json"
            qp = Path(tmpdir) / "queue.json"
            with mock.patch.object(_svc, "MANIFEST_PATH", mp), \
                 mock.patch.object(_svc, "TOOL_REGISTRY_PATH", rp), \
                 mock.patch.object(_svc, "REVIEW_QUEUE_PATH", qp):
                result = _svc.get_status()
            self.assertEqual(result["open_review_count"], 0)

    def test_status_session_count_zero_when_no_sessions(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            mp = Path(tmpdir) / "m.json"
            rp = Path(tmpdir) / "r.json"
            sp = Path(tmpdir) / "sessions.json"
            with mock.patch.object(_svc, "MANIFEST_PATH", mp), \
                 mock.patch.object(_svc, "TOOL_REGISTRY_PATH", rp), \
                 mock.patch.object(_svc, "SESSIONS_PATH", sp):
                result = _svc.get_status()
            self.assertEqual(result["session_count"], 0)


class ListToolsTest(unittest.TestCase):
    def _run(self, tools, enabled_only=False):
        with tempfile.TemporaryDirectory() as tmpdir:
            rp = Path(tmpdir) / "registry.json"
            _write_json(rp, _minimal_registry(tools))
            with mock.patch.object(_svc, "TOOL_REGISTRY_PATH", rp):
                return _svc.list_tools(enabled_only=enabled_only)

    def _two_tools(self):
        return [
            {"name": "a", "category": "file_read", "risk_level": "low",
             "access_mode": "always_allowed", "enabled": True, "description": "d", "manifest_field": "t.a"},
            {"name": "b", "category": "patch_proposal", "risk_level": "medium",
             "access_mode": "queue_required", "enabled": False, "description": "d", "manifest_field": "t.b"},
        ]

    def test_list_tools_returns_list(self):
        result = self._run(self._two_tools())
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)

    def test_enabled_only_filters_disabled_tools(self):
        result = self._run(self._two_tools(), enabled_only=True)
        self.assertEqual(len(result), 1)
        self.assertTrue(result[0]["enabled"])

    def test_all_returns_both(self):
        result = self._run(self._two_tools(), enabled_only=False)
        self.assertEqual(len(result), 2)

    def test_each_tool_has_required_fields(self):
        result = self._run(self._two_tools())
        for tool in result:
            for field in ("name", "category", "risk_level", "access_mode", "enabled"):
                self.assertIn(field, tool, msg=f"tool {tool.get('name')} missing {field!r}")


if __name__ == "__main__":
    unittest.main()
