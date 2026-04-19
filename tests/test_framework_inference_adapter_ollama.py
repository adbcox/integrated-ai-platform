"""Tests for OllamaInferenceAdapter in framework/inference_adapter.py."""

from __future__ import annotations

import os
import sys
import unittest
import unittest.mock
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from framework.inference_adapter import (
    OllamaInferenceAdapter,
    LocalHeuristicInferenceAdapter,
    InferenceRequest,
    InferenceResponse,
    build_inference_adapter,
)
from framework.backend_profiles import get_backend_profile


def _profile():
    return get_backend_profile("mac_local")


def _request(prompt: str = "explain WorkerRuntime job execution") -> InferenceRequest:
    return InferenceRequest(job_id="test-job-1", prompt=prompt)


class TestOllamaInferenceAdapterImport(unittest.TestCase):
    def test_importable_and_callable(self):
        self.assertTrue(callable(OllamaInferenceAdapter))


class TestOllamaInferenceAdapterInstantiation(unittest.TestCase):
    def test_instantiation_does_not_raise(self):
        try:
            OllamaInferenceAdapter(profile=_profile())
        except Exception as e:
            self.fail(f"Raised unexpected exception: {e}")

    def test_default_base_url_when_env_absent(self):
        with unittest.mock.patch.dict(os.environ, {}, clear=False):
            env = {k: v for k, v in os.environ.items() if k != "OLLAMA_API_BASE"}
            with unittest.mock.patch.dict(os.environ, env, clear=True):
                adapter = OllamaInferenceAdapter(profile=_profile())
        self.assertEqual(adapter._base_url, "http://localhost:11434")

    def test_default_model_when_env_absent(self):
        with unittest.mock.patch.dict(os.environ, {}, clear=False):
            env = {k: v for k, v in os.environ.items() if k != "OLLAMA_MODEL"}
            with unittest.mock.patch.dict(os.environ, env, clear=True):
                adapter = OllamaInferenceAdapter(profile=_profile())
        self.assertEqual(adapter._model, "qwen2.5-coder:14b")

    def test_ollama_api_base_env_var_read(self):
        with unittest.mock.patch.dict(os.environ, {"OLLAMA_API_BASE": "http://myhost:12345"}):
            adapter = OllamaInferenceAdapter(profile=_profile())
        self.assertEqual(adapter._base_url, "http://myhost:12345")

    def test_ollama_model_env_var_read(self):
        with unittest.mock.patch.dict(os.environ, {"OLLAMA_MODEL": "deepseek-coder-v2:latest"}):
            adapter = OllamaInferenceAdapter(profile=_profile())
        self.assertEqual(adapter._model, "deepseek-coder-v2:latest")


class TestOllamaInferenceAdapterRun(unittest.TestCase):
    def test_run_returns_inference_response(self):
        adapter = OllamaInferenceAdapter(profile=_profile(), base_url="http://localhost:19999/nonexistent")
        result = adapter.run(_request())
        self.assertIsInstance(result, InferenceResponse)
        self.assertIsInstance(result.output_text, str)
        self.assertIsInstance(result.backend, str)
        self.assertIsInstance(result.metadata, dict)

    def test_run_unreachable_url_falls_back_gracefully(self):
        adapter = OllamaInferenceAdapter(profile=_profile(), base_url="http://localhost:19999/nonexistent")
        try:
            result = adapter.run(_request())
        except Exception as e:
            self.fail(f"run() raised unexpected exception on network failure: {e}")

    def test_fallback_result_backend_is_profile_name(self):
        adapter = OllamaInferenceAdapter(profile=_profile(), base_url="http://localhost:19999/nonexistent")
        result = adapter.run(_request())
        self.assertEqual(result.backend, _profile().name)

    def test_run_with_empty_prompt_falls_back_gracefully(self):
        adapter = OllamaInferenceAdapter(profile=_profile(), base_url="http://localhost:19999/nonexistent")
        try:
            result = adapter.run(_request(prompt=""))
            self.assertIsInstance(result, InferenceResponse)
        except Exception as e:
            self.fail(f"run() raised on empty prompt: {e}")


class TestBuildInferenceAdapterOllama(unittest.TestCase):
    def test_mode_ollama_returns_ollama_adapter(self):
        adapter = build_inference_adapter(backend_profile="mac_local", mode="ollama")
        self.assertIsInstance(adapter, OllamaInferenceAdapter)

    def test_mode_heuristic_still_returns_local_heuristic(self):
        adapter = build_inference_adapter(backend_profile="mac_local", mode="heuristic")
        self.assertIsInstance(adapter, LocalHeuristicInferenceAdapter)


class TestSourceTextAssertions(unittest.TestCase):
    def _inference_source(self):
        return (Path(__file__).resolve().parents[1] / "framework" / "inference_adapter.py").read_text()

    def _bin_source(self):
        return (Path(__file__).resolve().parents[1] / "bin" / "framework_control_plane.py").read_text()

    def test_ollama_inference_adapter_in_source(self):
        self.assertIn("OllamaInferenceAdapter", self._inference_source())

    def test_ollama_api_base_in_source(self):
        self.assertIn("OLLAMA_API_BASE", self._inference_source())

    def test_api_chat_in_source(self):
        self.assertIn("api/chat", self._inference_source())

    def test_ollama_in_bin_inference_mode_choices(self):
        self.assertIn("ollama", self._bin_source())


if __name__ == "__main__":
    unittest.main()
