"""Tests for _phase3_extract_inference_response and context_bundle_inference_probe."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from framework.framework_control_plane import _phase3_extract_inference_response

_REQUIRED_KEYS = {"output_text", "backend", "inference_metadata", "output_chars", "has_content"}


class TestExtractInferenceResponseEmpty(unittest.TestCase):
    def test_empty_dict_returns_safe_defaults(self):
        r = _phase3_extract_inference_response({})
        self.assertEqual(set(r.keys()), _REQUIRED_KEYS)
        self.assertEqual(r["output_text"], "")
        self.assertEqual(r["backend"], "")
        self.assertEqual(r["inference_metadata"], {})
        self.assertEqual(r["output_chars"], 0)
        self.assertFalse(r["has_content"])

    def test_non_dict_returns_safe_defaults(self):
        r = _phase3_extract_inference_response(None)  # type: ignore[arg-type]
        self.assertEqual(set(r.keys()), _REQUIRED_KEYS)
        self.assertFalse(r["has_content"])

    def test_non_dict_does_not_raise(self):
        try:
            _phase3_extract_inference_response("bad")  # type: ignore[arg-type]
        except Exception as e:
            self.fail(f"Raised unexpected exception: {e}")


class TestExtractInferenceResponseFields(unittest.TestCase):
    def test_output_text_extracted(self):
        r = _phase3_extract_inference_response({"output": "hello world"})
        self.assertEqual(r["output_text"], "hello world")

    def test_output_chars_equals_len(self):
        r = _phase3_extract_inference_response({"output": "abc"})
        self.assertEqual(r["output_chars"], 3)

    def test_has_content_true_when_non_empty(self):
        r = _phase3_extract_inference_response({"output": "something"})
        self.assertTrue(r["has_content"])

    def test_has_content_false_when_whitespace_only(self):
        r = _phase3_extract_inference_response({"output": "   \n\t  "})
        self.assertFalse(r["has_content"])

    def test_backend_extracted(self):
        r = _phase3_extract_inference_response({"output": "x", "backend": "local_heuristic"})
        self.assertEqual(r["backend"], "local_heuristic")

    def test_inference_metadata_extracted_when_dict(self):
        meta = {"model": "qwen", "tokens": 42}
        r = _phase3_extract_inference_response({"inference_metadata": meta})
        self.assertEqual(r["inference_metadata"], meta)

    def test_inference_metadata_defaults_when_non_dict(self):
        r = _phase3_extract_inference_response({"inference_metadata": "not a dict"})
        self.assertEqual(r["inference_metadata"], {})

    def test_inference_metadata_defaults_when_absent(self):
        r = _phase3_extract_inference_response({"output": "x"})
        self.assertEqual(r["inference_metadata"], {})

    def test_output_text_not_truncated(self):
        long_text = "x" * 600
        r = _phase3_extract_inference_response({"output": long_text})
        self.assertEqual(len(r["output_text"]), 600)

    def test_all_required_keys_present(self):
        r = _phase3_extract_inference_response({"output": "hi", "backend": "b"})
        self.assertEqual(set(r.keys()), _REQUIRED_KEYS)


class TestInferenceResponseTemplate(unittest.TestCase):
    def test_template_has_no_phase2_typed_tools(self):
        from bin.framework_control_plane import _template_payload
        t = _template_payload("context_bundle_inference_probe")
        self.assertNotIn("phase2_typed_tools", t)

    def test_template_has_inference_prompt(self):
        from bin.framework_control_plane import _template_payload
        t = _template_payload("context_bundle_inference_probe")
        self.assertIn("inference_prompt", t)
        self.assertIsInstance(t["inference_prompt"], str)
        self.assertGreater(len(t["inference_prompt"]), 0)


class TestInferenceResponseMeta(unittest.TestCase):
    def test_importable_from_framework(self):
        from framework.framework_control_plane import _phase3_extract_inference_response as fn
        self.assertTrue(callable(fn))

    def test_in_all(self):
        import framework.framework_control_plane as m
        self.assertIn("_phase3_extract_inference_response", m.__all__)


if __name__ == "__main__":
    unittest.main()
