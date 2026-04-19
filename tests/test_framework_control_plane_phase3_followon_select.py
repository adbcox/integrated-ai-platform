"""Tests for _phase3_select_followon_template and related bin helpers."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from framework.framework_control_plane import _phase3_select_followon_template

_KNOWN_TEMPLATES = frozenset({
    "retrieval_probe",
    "read_after_retrieval",
    "context_bundle_probe",
    "context_bundle_inference_probe",
})


class TestPhase3SelectFollowonTemplate(unittest.TestCase):
    def test_empty_dict_returns_retrieval_probe(self):
        self.assertEqual(_phase3_select_followon_template({}), "retrieval_probe")

    def test_ready_returns_context_bundle_inference_probe(self):
        self.assertEqual(_phase3_select_followon_template({"action": "ready"}), "context_bundle_inference_probe")

    def test_insufficient_context_returns_read_after_retrieval(self):
        self.assertEqual(_phase3_select_followon_template({"action": "insufficient_context"}), "read_after_retrieval")

    def test_refine_retrieval_returns_retrieval_probe(self):
        self.assertEqual(_phase3_select_followon_template({"action": "refine_retrieval"}), "retrieval_probe")

    def test_no_context_returns_retrieval_probe(self):
        self.assertEqual(_phase3_select_followon_template({"action": "no_context"}), "retrieval_probe")

    def test_uppercase_ready_returns_retrieval_probe(self):
        self.assertEqual(_phase3_select_followon_template({"action": "READY"}), "retrieval_probe")

    def test_empty_action_string_returns_retrieval_probe(self):
        self.assertEqual(_phase3_select_followon_template({"action": ""}), "retrieval_probe")

    def test_none_input_returns_retrieval_probe(self):
        self.assertEqual(_phase3_select_followon_template(None), "retrieval_probe")  # type: ignore[arg-type]

    def test_none_input_does_not_raise(self):
        try:
            _phase3_select_followon_template(None)  # type: ignore[arg-type]
        except Exception as e:
            self.fail(f"Raised unexpected exception: {e}")

    def test_all_valid_actions_return_nonempty(self):
        for action in ("ready", "insufficient_context", "refine_retrieval", "no_context"):
            result = _phase3_select_followon_template({"action": action})
            self.assertTrue(result, f"action={action!r} returned empty string")

    def test_all_valid_actions_return_known_template(self):
        for action in ("ready", "insufficient_context", "refine_retrieval", "no_context"):
            result = _phase3_select_followon_template({"action": action})
            self.assertIn(result, _KNOWN_TEMPLATES, f"action={action!r} returned unknown template {result!r}")

    def test_importable_from_framework(self):
        from framework.framework_control_plane import _phase3_select_followon_template as fn
        self.assertTrue(callable(fn))

    def test_in_all(self):
        import framework.framework_control_plane as m
        self.assertIn("_phase3_select_followon_template", m.__all__)


class TestLoadPhase3Followon(unittest.TestCase):
    def setUp(self):
        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

    def _get_loader(self):
        from bin.framework_control_plane import _load_phase3_followon
        return _load_phase3_followon

    def test_missing_path_returns_empty_dict(self):
        loader = self._get_loader()
        result = loader(Path("/tmp/__nonexistent_phase3_fw__.json"))
        self.assertEqual(result, {})

    def test_valid_json_dict_returns_dict(self):
        loader = self._get_loader()
        with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False, encoding="utf-8") as f:
            json.dump({"template": "retrieval_probe", "action": "no_context"}, f)
            tmp = Path(f.name)
        try:
            result = loader(tmp)
            self.assertEqual(result, {"template": "retrieval_probe", "action": "no_context"})
        finally:
            tmp.unlink(missing_ok=True)

    def test_malformed_json_returns_empty_dict(self):
        loader = self._get_loader()
        with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False, encoding="utf-8") as f:
            f.write("{not valid json")
            tmp = Path(f.name)
        try:
            result = loader(tmp)
            self.assertEqual(result, {})
        finally:
            tmp.unlink(missing_ok=True)

    def test_non_dict_json_returns_empty_dict(self):
        loader = self._get_loader()
        with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False, encoding="utf-8") as f:
            json.dump(["list", "not", "dict"], f)
            tmp = Path(f.name)
        try:
            result = loader(tmp)
            self.assertEqual(result, {})
        finally:
            tmp.unlink(missing_ok=True)


class TestPhase3FollowonTemplateDispatch(unittest.TestCase):
    def setUp(self):
        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

    def test_template_payload_returns_dict(self):
        from bin.framework_control_plane import _template_payload
        result = _template_payload("phase3_followon")
        self.assertIsInstance(result, dict)

    def test_template_payload_has_resolved_template_key(self):
        from bin.framework_control_plane import _template_payload
        result = _template_payload("phase3_followon")
        self.assertIn("_phase3_followon_resolved_template", result)

    def test_resolved_template_is_known(self):
        from bin.framework_control_plane import _template_payload
        result = _template_payload("phase3_followon")
        self.assertIn(result["_phase3_followon_resolved_template"], _KNOWN_TEMPLATES)


if __name__ == "__main__":
    unittest.main()
