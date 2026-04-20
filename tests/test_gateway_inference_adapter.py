"""Offline tests for framework/gateway_inference_adapter.py.

All tests pass without a live Ollama daemon.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))


def _mac_profile():
    from framework.backend_profiles import get_backend_profile
    return get_backend_profile("mac_local")


def _threadripper_profile():
    from framework.backend_profiles import get_backend_profile
    return get_backend_profile("threadripper_local")


def _multi_host_profile():
    from framework.backend_profiles import get_backend_profile
    return get_backend_profile("multi_host_future")


def _make_request(job_id: str = "job-001", prompt: str = "add guard clause"):
    from framework.inference_adapter import InferenceRequest
    return InferenceRequest(job_id=job_id, prompt=prompt)


class ProfileMappingTest(unittest.TestCase):
    def _mapping(self):
        from framework.gateway_inference_adapter import BACKEND_TO_GATEWAY_PROFILE
        return BACKEND_TO_GATEWAY_PROFILE

    def test_mac_local_maps_to_fast(self):
        self.assertEqual(self._mapping()["mac_local"], "fast")

    def test_threadripper_local_maps_to_balanced(self):
        self.assertEqual(self._mapping()["threadripper_local"], "balanced")

    def test_multi_host_future_maps_to_hard(self):
        self.assertEqual(self._mapping()["multi_host_future"], "hard")

    def test_unknown_name_falls_back_to_balanced(self):
        from framework.gateway_inference_adapter import BACKEND_TO_GATEWAY_PROFILE
        result = BACKEND_TO_GATEWAY_PROFILE.get("unknown_profile", "balanced")
        self.assertEqual(result, "balanced")


class GatewayAdapterProtocolTest(unittest.TestCase):
    def _build(self):
        from framework.gateway_inference_adapter import build_gateway_adapter
        return build_gateway_adapter(_mac_profile(), force_heuristic=True)

    def test_adapter_exposes_profile(self):
        adapter = self._build()
        self.assertIsNotNone(adapter.profile)
        self.assertEqual(adapter.profile.name, "mac_local")

    def test_run_returns_inference_response(self):
        from framework.inference_adapter import InferenceResponse
        adapter = self._build()
        result = adapter.run(_make_request())
        self.assertIsInstance(result, InferenceResponse)

    def test_result_has_backend(self):
        adapter = self._build()
        result = adapter.run(_make_request())
        self.assertTrue(result.backend)

    def test_result_has_output_text(self):
        adapter = self._build()
        result = adapter.run(_make_request())
        self.assertIsInstance(result.output_text, str)

    def test_result_has_metadata(self):
        adapter = self._build()
        result = adapter.run(_make_request())
        self.assertIsInstance(result.metadata, dict)

    def test_metadata_has_success_true(self):
        adapter = self._build()
        result = adapter.run(_make_request())
        self.assertIn("success", result.metadata)
        self.assertTrue(result.metadata["success"])

    def test_metadata_has_telemetry(self):
        adapter = self._build()
        result = adapter.run(_make_request())
        self.assertIn("telemetry", result.metadata)


class GatewayAdapterHeuristicTest(unittest.TestCase):
    def _build(self, profile=None):
        from framework.gateway_inference_adapter import build_gateway_adapter
        return build_gateway_adapter(
            profile or _mac_profile(),
            force_heuristic=True,
        )

    def test_run_returns_inference_response(self):
        from framework.inference_adapter import InferenceResponse
        adapter = self._build()
        result = adapter.run(_make_request())
        self.assertIsInstance(result, InferenceResponse)

    def test_output_text_contains_heuristic_marker(self):
        adapter = self._build()
        result = adapter.run(_make_request())
        self.assertIn("[heuristic]", result.output_text)

    def test_job_id_forwarded_as_requested_by(self):
        adapter = self._build()
        result = adapter.run(_make_request(job_id="job-xyz"))
        telemetry = result.metadata.get("telemetry", {})
        # requested_by is recorded in gateway telemetry as requester
        self.assertIsInstance(telemetry, dict)

    def test_backend_equals_profile_name(self):
        adapter = self._build(_mac_profile())
        result = adapter.run(_make_request())
        self.assertEqual(result.backend, "mac_local")

    def test_threadripper_backend_name(self):
        from framework.gateway_inference_adapter import build_gateway_adapter
        adapter = build_gateway_adapter(_threadripper_profile(), force_heuristic=True)
        result = adapter.run(_make_request())
        self.assertEqual(result.backend, "threadripper_local")


class GatewayAdapterErrorPropagationTest(unittest.TestCase):
    def _build_with_raising_executor(self):
        from framework.gateway_inference_adapter import GatewayInferenceAdapter
        from framework.inference_gateway import InferenceGateway

        def _bad_executor(req, profile):
            raise RuntimeError("simulated executor failure")

        gateway = InferenceGateway(executor=_bad_executor)
        return GatewayInferenceAdapter(profile=_mac_profile(), gateway=gateway)

    def test_returns_inference_response_on_error(self):
        from framework.inference_adapter import InferenceResponse
        adapter = self._build_with_raising_executor()
        result = adapter.run(_make_request())
        self.assertIsInstance(result, InferenceResponse)

    def test_output_text_is_empty_on_error(self):
        adapter = self._build_with_raising_executor()
        result = adapter.run(_make_request())
        self.assertEqual(result.output_text, "")

    def test_metadata_success_is_false_on_error(self):
        adapter = self._build_with_raising_executor()
        result = adapter.run(_make_request())
        self.assertIn("success", result.metadata)
        self.assertFalse(result.metadata["success"])

    def test_metadata_includes_error_field_on_error(self):
        adapter = self._build_with_raising_executor()
        result = adapter.run(_make_request())
        self.assertIn("error", result.metadata)
        self.assertIn("simulated executor failure", result.metadata["error"])


if __name__ == "__main__":
    unittest.main()
