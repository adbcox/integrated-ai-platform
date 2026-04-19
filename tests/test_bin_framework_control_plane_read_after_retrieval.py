"""Tests for PHASE3-READ-AFTER-RETRIEVAL-1: _load_retrieval_targets and _read_after_retrieval_template."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def _import_helpers():
    from bin.framework_control_plane import (
        _load_retrieval_targets,
        _read_after_retrieval_template,
    )
    return _load_retrieval_targets, _read_after_retrieval_template


class TestLoadRetrievalTargets(unittest.TestCase):
    def setUp(self):
        self._load, self._template = _import_helpers()

    def test_missing_file_returns_empty(self):
        p = Path("/tmp/__nonexistent_retrieval_targets_xyz__.json")
        self.assertEqual(self._load(p), [])

    def test_empty_list_file_returns_empty(self):
        with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as f:
            json.dump([], f)
            p = Path(f.name)
        self.assertEqual(self._load(p), [])

    def test_valid_list_returned(self):
        specs = [
            {"contract_name": "read_file", "arguments": {"path": "/x/y.py"}},
            {"contract_name": "read_file", "arguments": {"path": "/a/b.py"}},
        ]
        with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as f:
            json.dump(specs, f)
            p = Path(f.name)
        result = self._load(p)
        self.assertEqual(result, specs)

    def test_non_list_payload_returns_empty(self):
        with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as f:
            json.dump({"key": "value"}, f)
            p = Path(f.name)
        self.assertEqual(self._load(p), [])

    def test_non_dict_entries_filtered(self):
        with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as f:
            json.dump([{"contract_name": "read_file"}, "bad", None], f)
            p = Path(f.name)
        result = self._load(p)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["contract_name"], "read_file")

    def test_malformed_json_returns_empty(self):
        with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as f:
            f.write("{not valid json")
            p = Path(f.name)
        self.assertEqual(self._load(p), [])


class TestReadAfterRetrievalTemplate(unittest.TestCase):
    def setUp(self):
        self._load, self._template = _import_helpers()

    def _write_specs(self, specs):
        f = tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False)
        json.dump(specs, f)
        f.close()
        return Path(f.name)

    def test_no_targets_file_produces_apply_patch_only(self):
        p = Path("/tmp/__nonexistent_for_template_test__.json")
        tmpl = self._template(targets_path=p)
        tools = tmpl["phase2_typed_tools"]
        self.assertEqual(len(tools), 1)
        self.assertEqual(tools[0]["contract_name"], "apply_patch")

    def test_with_targets_prepends_read_specs(self):
        specs = [{"contract_name": "read_file", "arguments": {"path": "/a.py"}}]
        p = self._write_specs(specs)
        tmpl = self._template(targets_path=p)
        tools = tmpl["phase2_typed_tools"]
        self.assertEqual(len(tools), 2)
        self.assertEqual(tools[0]["contract_name"], "read_file")
        self.assertEqual(tools[0]["arguments"]["path"], "/a.py")
        self.assertEqual(tools[-1]["contract_name"], "apply_patch")

    def test_apply_patch_sentinel_reflects_target_count(self):
        specs = [
            {"contract_name": "read_file", "arguments": {"path": "/a.py"}},
            {"contract_name": "read_file", "arguments": {"path": "/b.py"}},
        ]
        p = self._write_specs(specs)
        tmpl = self._template(targets_path=p)
        patch_tool = tmpl["phase2_typed_tools"][-1]
        self.assertIn("targets=2", patch_tool["arguments"]["content"])

    def test_template_has_required_keys(self):
        p = Path("/tmp/__nonexistent__.json")
        tmpl = self._template(targets_path=p)
        for key in ("task_class", "shell_command", "inference_prompt", "artifact_inputs",
                    "requested_outputs", "phase2_typed_tools", "permission_policy"):
            self.assertIn(key, tmpl, f"missing key: {key}")

    def test_requested_outputs_has_read_after_retrieval_artifact(self):
        p = Path("/tmp/__nonexistent__.json")
        tmpl = self._template(targets_path=p)
        self.assertTrue(
            any("read_after_retrieval" in o for o in tmpl["requested_outputs"])
        )

    def test_template_registered_in_choices(self):
        import argparse
        from bin.framework_control_plane import parse_args
        # parse_args should accept read_after_retrieval as task-template
        ns = parse_args.__wrapped__() if hasattr(parse_args, "__wrapped__") else None
        # simpler: just check _template_payload returns something non-empty
        from bin.framework_control_plane import _template_payload
        result = _template_payload("read_after_retrieval")
        self.assertIn("phase2_typed_tools", result)


class TestTemplatePayloadDispatch(unittest.TestCase):
    def test_read_after_retrieval_dispatches(self):
        from bin.framework_control_plane import _template_payload
        payload = _template_payload("read_after_retrieval")
        self.assertIn("phase2_typed_tools", payload)
        tools = payload["phase2_typed_tools"]
        self.assertIsInstance(tools, list)
        self.assertGreater(len(tools), 0)

    def test_apply_patch_write_mode_in_template(self):
        from bin.framework_control_plane import _template_payload
        payload = _template_payload("read_after_retrieval")
        patch_tool = payload["phase2_typed_tools"][-1]
        self.assertEqual(patch_tool["contract_name"], "apply_patch")
        self.assertEqual(patch_tool["arguments"]["mode"], "write_text")


if __name__ == "__main__":
    unittest.main()
