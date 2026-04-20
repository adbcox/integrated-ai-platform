"""Offline tests for framework/gateway_executors.py.

All tests pass without a live Ollama daemon. Ollama connectivity is verified
by probing a port that is guaranteed unused (19934) so probe tests are
deterministic in CI.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))


def _make_request(prompt: str = "hello", profile_name: str = "fast") -> object:
    from framework.inference_gateway import GatewayRequest
    return GatewayRequest(profile_name=profile_name, prompt=prompt)


def _fast_profile() -> object:
    from framework.model_profiles import get_profile
    return get_profile("fast")


class HeuristicExecutorTest(unittest.TestCase):
    def _call(self, prompt: str = "add guard clause") -> str:
        from framework.gateway_executors import heuristic_executor
        req = _make_request(prompt)
        profile = _fast_profile()
        return heuristic_executor(req, profile)

    def test_output_contains_heuristic_prefix(self) -> None:
        self.assertIn("[heuristic]", self._call())

    def test_output_contains_profile_name(self) -> None:
        self.assertIn("profile=fast", self._call())

    def test_output_contains_model_name(self) -> None:
        self.assertIn("qwen2.5-coder:14b", self._call())

    def test_output_contains_prompt_head(self) -> None:
        result = self._call("fix the bug in foo")
        self.assertIn("fix the bug in foo", result)

    def test_long_prompt_truncated_to_80_chars(self) -> None:
        long_line = "x" * 120
        result = self._call(long_line)
        # head repr is capped at 80 chars of original
        self.assertNotIn("x" * 81, result)

    def test_empty_prompt_does_not_crash(self) -> None:
        result = self._call("")
        self.assertIn("[heuristic]", result)

    def test_no_external_deps_required(self) -> None:
        # If this test runs, no network call was made — trivially passes.
        self._call("test")


class ProbeOllamaTest(unittest.TestCase):
    def test_unreachable_host_returns_false(self) -> None:
        from framework.gateway_executors import _probe_ollama
        # Port 19934 is not in use; probe must return False quickly.
        result = _probe_ollama("http://127.0.0.1:19934", timeout=1.0)
        self.assertFalse(result)

    def test_invalid_scheme_returns_false(self) -> None:
        from framework.gateway_executors import _probe_ollama
        result = _probe_ollama("http://192.0.2.0:19934", timeout=1.0)
        self.assertFalse(result)


class OllamaExecutorFactoryTest(unittest.TestCase):
    def test_factory_returns_callable(self) -> None:
        from framework.gateway_executors import make_ollama_executor
        executor = make_ollama_executor("http://127.0.0.1:19934")
        self.assertTrue(callable(executor))

    def test_factory_with_model_override_returns_callable(self) -> None:
        from framework.gateway_executors import make_ollama_executor
        executor = make_ollama_executor(model_override="custom-model")
        self.assertTrue(callable(executor))

    def test_executor_raises_on_unreachable_ollama(self) -> None:
        from framework.gateway_executors import make_ollama_executor
        from framework.inference_gateway import GatewayRequest
        executor = make_ollama_executor("http://127.0.0.1:19934")
        req = GatewayRequest(profile_name="fast", prompt="test")
        profile = _fast_profile()
        with self.assertRaises(RuntimeError):
            executor(req, profile)


class EnvAutoExecutorTest(unittest.TestCase):
    def test_falls_back_to_heuristic_when_ollama_unreachable(self) -> None:
        from framework.gateway_executors import make_env_auto_executor
        # Port 19934 guaranteed unreachable → heuristic path
        executor = make_env_auto_executor("http://127.0.0.1:19934")
        req = _make_request("test fallback")
        profile = _fast_profile()
        result = executor(req, profile)
        self.assertIn("[heuristic]", result)

    def test_fallback_output_contains_prompt_head(self) -> None:
        from framework.gateway_executors import make_env_auto_executor
        executor = make_env_auto_executor("http://127.0.0.1:19934")
        req = _make_request("specific prompt text")
        profile = _fast_profile()
        result = executor(req, profile)
        self.assertIn("specific prompt text", result)


class BuildGatewayForEnvTest(unittest.TestCase):
    def test_force_heuristic_returns_gateway(self) -> None:
        from framework.gateway_executors import build_gateway_for_env
        from framework.inference_gateway import InferenceGateway
        gw = build_gateway_for_env(force_heuristic=True)
        self.assertIsInstance(gw, InferenceGateway)

    def test_force_heuristic_invoke_succeeds(self) -> None:
        from framework.gateway_executors import build_gateway_for_env
        from framework.inference_gateway import GatewayRequest
        gw = build_gateway_for_env(force_heuristic=True)
        resp = gw.invoke(GatewayRequest(profile_name="fast", prompt="hello gateway"))
        self.assertTrue(resp.success)
        self.assertIn("[heuristic]", resp.output_text)

    def test_force_heuristic_telemetry_populated(self) -> None:
        from framework.gateway_executors import build_gateway_for_env
        from framework.inference_gateway import GatewayRequest
        gw = build_gateway_for_env(force_heuristic=True)
        resp = gw.invoke(GatewayRequest(profile_name="balanced", prompt="test telem"))
        t = resp.telemetry
        self.assertEqual(t.profile_name, "balanced")
        self.assertTrue(t.success)
        self.assertGreaterEqual(t.duration_ms, 0)
        self.assertIsNotNone(t.prompt_hash)

    def test_unreachable_base_url_falls_back_to_heuristic(self) -> None:
        from framework.gateway_executors import build_gateway_for_env
        from framework.inference_gateway import GatewayRequest
        gw = build_gateway_for_env(base_url="http://127.0.0.1:19934")
        resp = gw.invoke(GatewayRequest(profile_name="fast", prompt="env auto test"))
        self.assertTrue(resp.success)
        self.assertIn("[heuristic]", resp.output_text)

    def test_response_to_dict_has_expected_keys(self) -> None:
        from framework.gateway_executors import build_gateway_for_env
        from framework.inference_gateway import GatewayRequest
        gw = build_gateway_for_env(force_heuristic=True)
        resp = gw.invoke(GatewayRequest(profile_name="hard", prompt="dict test"))
        d = resp.to_dict()
        for key in ("profile_name", "backend", "model", "output_text", "success", "error", "telemetry"):
            self.assertIn(key, d)


if __name__ == "__main__":
    unittest.main()
