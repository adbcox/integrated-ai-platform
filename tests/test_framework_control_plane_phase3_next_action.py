"""Tests for _phase3_derive_next_action."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from framework.framework_control_plane import _phase3_derive_next_action

_REQUIRED_KEYS = {"action", "reason", "context_adequate", "total_files", "total_symbols", "inference_has_content"}


def _bundle(prompt_ready=True, total_files=2, total_symbols=3):
    return {
        "query": "_execute_job",
        "total_files": total_files,
        "total_symbols": total_symbols,
        "files_with_symbols": total_files,
        "files": [],
        "top_file": "framework/x.py",
        "top_file_symbol_count": total_symbols,
        "prompt_ready": prompt_ready,
    }


def _inference(has_content=True, output_text="some output"):
    return {
        "output_text": output_text if has_content else "",
        "backend": "local_heuristic",
        "inference_metadata": {},
        "output_chars": len(output_text) if has_content else 0,
        "has_content": has_content,
    }


class TestNextActionNoContext(unittest.TestCase):
    def test_empty_bundle_gives_no_context(self):
        r = _phase3_derive_next_action({}, {})
        self.assertEqual(r["action"], "no_context")
        self.assertFalse(r["context_adequate"])

    def test_prompt_ready_false_gives_no_context(self):
        r = _phase3_derive_next_action(_bundle(prompt_ready=False), _inference())
        self.assertEqual(r["action"], "no_context")

    def test_non_dict_bundle_gives_no_context(self):
        r = _phase3_derive_next_action(None, _inference())  # type: ignore[arg-type]
        self.assertEqual(r["action"], "no_context")
        self.assertFalse(r["context_adequate"])

    def test_non_dict_bundle_does_not_raise(self):
        try:
            _phase3_derive_next_action(None, None)  # type: ignore[arg-type]
        except Exception as e:
            self.fail(f"Raised unexpected exception: {e}")


class TestNextActionInsufficientContext(unittest.TestCase):
    def test_empty_inference_response_gives_insufficient(self):
        r = _phase3_derive_next_action(_bundle(), {})
        self.assertEqual(r["action"], "insufficient_context")
        self.assertFalse(r["context_adequate"])

    def test_has_content_false_gives_insufficient(self):
        r = _phase3_derive_next_action(_bundle(), _inference(has_content=False))
        self.assertEqual(r["action"], "insufficient_context")

    def test_non_dict_inference_gives_insufficient_or_no_context(self):
        r = _phase3_derive_next_action(_bundle(), None)  # type: ignore[arg-type]
        self.assertIn(r["action"], {"no_context", "insufficient_context"})
        self.assertFalse(r["context_adequate"])


class TestNextActionRefineRetrieval(unittest.TestCase):
    def test_total_symbols_zero_gives_refine(self):
        r = _phase3_derive_next_action(_bundle(total_symbols=0, total_files=2), _inference())
        self.assertEqual(r["action"], "refine_retrieval")
        self.assertIn("symbols", r["reason"])

    def test_symbols_check_fires_before_files_check(self):
        r = _phase3_derive_next_action(_bundle(total_symbols=0, total_files=2), _inference())
        self.assertEqual(r["action"], "refine_retrieval")
        self.assertIn("symbols", r["reason"])

    def test_total_files_zero_gives_refine(self):
        r = _phase3_derive_next_action(_bundle(total_symbols=3, total_files=0), _inference())
        self.assertEqual(r["action"], "refine_retrieval")


class TestNextActionReady(unittest.TestCase):
    def test_all_good_gives_ready(self):
        r = _phase3_derive_next_action(_bundle(total_symbols=3, total_files=2), _inference())
        self.assertEqual(r["action"], "ready")
        self.assertTrue(r["context_adequate"])

    def test_context_adequate_true_only_when_ready(self):
        for action, bundle, inference in [
            ("no_context", {}, {}),
            ("insufficient_context", _bundle(), _inference(has_content=False)),
            ("refine_retrieval", _bundle(total_symbols=0), _inference()),
            ("ready", _bundle(), _inference()),
        ]:
            r = _phase3_derive_next_action(bundle, inference)
            self.assertEqual(r["context_adequate"], r["action"] == "ready",
                             f"action={r['action']!r}: expected context_adequate={r['action']=='ready'}")


class TestNextActionFieldValues(unittest.TestCase):
    def test_total_files_in_result(self):
        r = _phase3_derive_next_action(_bundle(total_files=5, total_symbols=3), _inference())
        self.assertEqual(r["total_files"], 5)

    def test_total_symbols_in_result(self):
        r = _phase3_derive_next_action(_bundle(total_files=2, total_symbols=7), _inference())
        self.assertEqual(r["total_symbols"], 7)

    def test_inference_has_content_in_result(self):
        r = _phase3_derive_next_action(_bundle(), _inference(has_content=True))
        self.assertTrue(r["inference_has_content"])

    def test_all_required_keys_present(self):
        r = _phase3_derive_next_action(_bundle(), _inference())
        self.assertEqual(set(r.keys()), _REQUIRED_KEYS)

    def test_importable_from_framework(self):
        from framework.framework_control_plane import _phase3_derive_next_action as fn
        self.assertTrue(callable(fn))

    def test_in_all(self):
        import framework.framework_control_plane as m
        self.assertIn("_phase3_derive_next_action", m.__all__)


if __name__ == "__main__":
    unittest.main()
