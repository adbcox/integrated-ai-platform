"""Offline regression for framework.inference_gateway."""

from __future__ import annotations

import unittest

from framework.inference_gateway import (
    GatewayRequest,
    GatewayResponse,
    InferenceGateway,
)
from framework.model_profiles import get_profile
from framework.runtime_telemetry_schema import InferenceTelemetry


class InferenceGatewayTest(unittest.TestCase):
    def test_default_executor_produces_telemetry(self) -> None:
        gateway = InferenceGateway()
        response = gateway.invoke(
            GatewayRequest(profile_name="fast", prompt="hello")
        )
        self.assertIsInstance(response, GatewayResponse)
        self.assertEqual(response.profile_name, "fast")
        self.assertTrue(response.success)
        self.assertEqual(response.error, "")
        self.assertIsInstance(response.telemetry, InferenceTelemetry)
        self.assertEqual(response.telemetry.backend, get_profile("fast").backend)
        self.assertEqual(response.telemetry.model, get_profile("fast").model)
        self.assertGreater(len(response.telemetry.prompt_hash), 0)
        self.assertTrue(response.telemetry.started_at)
        self.assertTrue(response.telemetry.completed_at)
        self.assertGreaterEqual(response.telemetry.duration_ms, 0)

    def test_injectable_executor_is_called(self) -> None:
        seen = {}

        def fake_executor(request, profile):
            seen["profile"] = profile.profile_name
            seen["prompt"] = request.prompt
            return f"fake-output for {profile.profile_name}"

        gateway = InferenceGateway(executor=fake_executor)
        response = gateway.invoke(
            GatewayRequest(profile_name="balanced", prompt="refactor x")
        )
        self.assertEqual(seen["profile"], "balanced")
        self.assertEqual(seen["prompt"], "refactor x")
        self.assertEqual(response.output_text, "fake-output for balanced")
        self.assertTrue(response.success)

    def test_executor_error_is_reported_not_raised(self) -> None:
        def bad_executor(request, profile):
            raise RuntimeError("backend down")

        gateway = InferenceGateway(executor=bad_executor)
        response = gateway.invoke(
            GatewayRequest(profile_name="fast", prompt="x")
        )
        self.assertFalse(response.success)
        self.assertIn("backend down", response.error)
        self.assertFalse(response.telemetry.success)
        self.assertIn("backend down", response.telemetry.error)

    def test_resolve_unknown_profile_raises(self) -> None:
        gateway = InferenceGateway()
        with self.assertRaises(KeyError):
            gateway.resolve("does_not_exist")

    def test_prompt_hash_is_deterministic(self) -> None:
        gateway = InferenceGateway()
        a = gateway.invoke(GatewayRequest(profile_name="fast", prompt="same"))
        b = gateway.invoke(GatewayRequest(profile_name="fast", prompt="same"))
        self.assertEqual(a.telemetry.prompt_hash, b.telemetry.prompt_hash)


if __name__ == "__main__":
    unittest.main()
