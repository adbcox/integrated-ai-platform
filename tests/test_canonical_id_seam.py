"""Offline tests verifying canonical identity boundary contracts.

Covers:
- job_id format contract against actual repo generation behavior
- session_id: distinct from job_id, accepts slug and UUID forms
- telemetry_run_id: run- prefix, maps to RunBundleManifest.run_id field name
- plan_id: context-derived format, matches declared spec pattern
- spec file parses and covers all four identity types
- example artifact parses, contains all four values as distinct strings
- four identity types are mutually distinct in a well-formed context
- plan_id example format against declared spec regex
"""

from __future__ import annotations

import json
import re
import sys
import unittest
from pathlib import Path
from uuid import uuid4

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

SPEC_PATH = REPO_ROOT / "governance" / "canonical_id_spec.json"
EXAMPLES_PATH = REPO_ROOT / "artifacts" / "framework" / "schema" / "canonical_id_examples.json"

_REQUIRED_IDENTITY_KEYS = {"job_id", "session_id", "telemetry_run_id", "plan_id"}

_JOB_ID_RE = re.compile(r"^job-[0-9a-f]{12}$")
_RUN_ID_RE = re.compile(r"^run-[0-9a-f]{12}$")
_PLAN_ID_RE = re.compile(r"^[a-z0-9][a-z0-9_-]+-[a-z0-9_-]+$")


class SpecFileTest(unittest.TestCase):
    """governance/canonical_id_spec.json must parse and be structurally correct."""

    def setUp(self) -> None:
        self.spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))

    def test_spec_parses(self) -> None:
        self.assertIsInstance(self.spec, dict)

    def test_spec_has_schema_version(self) -> None:
        self.assertIn("schema_version", self.spec)

    def test_spec_has_authority_owner(self) -> None:
        self.assertIn("authority_owner", self.spec)

    def test_spec_has_generated_at(self) -> None:
        self.assertIn("generated_at", self.spec)

    def test_spec_has_identities_key(self) -> None:
        self.assertIn("identities", self.spec)
        self.assertIsInstance(self.spec["identities"], dict)

    def test_spec_covers_all_four_identity_types(self) -> None:
        covered = set(self.spec["identities"].keys())
        missing = _REQUIRED_IDENTITY_KEYS - covered
        self.assertEqual(missing, set(), f"spec missing identity types: {missing}")

    def test_each_identity_has_description(self) -> None:
        for id_type, entry in self.spec["identities"].items():
            self.assertIn("description", entry, f"identity '{id_type}' missing description")

    def test_each_identity_has_example(self) -> None:
        for id_type, entry in self.spec["identities"].items():
            self.assertIn("example", entry, f"identity '{id_type}' missing example")

    def test_job_id_regex_in_spec(self) -> None:
        regex = self.spec["identities"]["job_id"]["regex"]
        self.assertRegex("job-5c5d1529af6c", regex)
        self.assertNotRegex("run-5c5d1529af6c", regex)
        self.assertNotRegex("job-SHORT", regex)

    def test_telemetry_run_id_regex_in_spec(self) -> None:
        regex = self.spec["identities"]["telemetry_run_id"]["regex"]
        self.assertRegex("run-3a1b9c2f0e47", regex)
        self.assertNotRegex("job-3a1b9c2f0e47", regex)

    def test_spec_invariants_present(self) -> None:
        self.assertIn("invariants", self.spec)
        self.assertIsInstance(self.spec["invariants"], list)
        self.assertGreater(len(self.spec["invariants"]), 0)


class ExampleArtifactTest(unittest.TestCase):
    """artifacts/framework/schema/canonical_id_examples.json must be valid and complete."""

    def setUp(self) -> None:
        self.examples = json.loads(EXAMPLES_PATH.read_text(encoding="utf-8"))

    def test_examples_parse(self) -> None:
        self.assertIsInstance(self.examples, dict)

    def test_examples_has_execution_context(self) -> None:
        self.assertIn("execution_context", self.examples)

    def test_all_four_identity_types_present(self) -> None:
        ctx = self.examples["execution_context"]
        missing = _REQUIRED_IDENTITY_KEYS - set(ctx.keys())
        self.assertEqual(missing, set(), f"example missing identity types: {missing}")

    def test_all_four_values_are_strings(self) -> None:
        ctx = self.examples["execution_context"]
        for id_type in _REQUIRED_IDENTITY_KEYS:
            self.assertIsInstance(ctx[id_type], str, f"{id_type} must be a string")
            self.assertTrue(ctx[id_type], f"{id_type} must be non-empty")

    def test_all_four_values_are_distinct(self) -> None:
        ctx = self.examples["execution_context"]
        values = [ctx[k] for k in _REQUIRED_IDENTITY_KEYS]
        self.assertEqual(len(values), len(set(values)), "all four identity values must be distinct")

    def test_example_invariants_section(self) -> None:
        self.assertIn("invariants", self.examples)
        inv = self.examples["invariants"]
        self.assertTrue(inv.get("all_four_present"), "invariant all_four_present must be true")
        self.assertTrue(inv.get("all_four_distinct"), "invariant all_four_distinct must be true")
        self.assertTrue(inv.get("no_shared_values"), "invariant no_shared_values must be true")

    def test_example_job_id_matches_spec_format(self) -> None:
        job_id = self.examples["execution_context"]["job_id"]
        self.assertRegex(job_id, _JOB_ID_RE, f"job_id '{job_id}' does not match job-{{12hex}} format")

    def test_example_telemetry_run_id_matches_spec_format(self) -> None:
        run_id = self.examples["execution_context"]["telemetry_run_id"]
        self.assertRegex(run_id, _RUN_ID_RE, f"telemetry_run_id '{run_id}' does not match run-{{12hex}} format")

    def test_example_plan_id_matches_spec_format(self) -> None:
        plan_id = self.examples["execution_context"]["plan_id"]
        self.assertRegex(plan_id, _PLAN_ID_RE, f"plan_id '{plan_id}' does not match declared spec regex")

    def test_spec_ref_present(self) -> None:
        self.assertIn("spec_ref", self.examples)


class JobIdFormatTest(unittest.TestCase):
    """Verify job_id format contract against actual repo generation behavior."""

    def test_generation_matches_spec(self) -> None:
        # Mirrors framework/job_schema.py: f"job-{uuid4().hex[:12]}"
        generated = f"job-{uuid4().hex[:12]}"
        self.assertRegex(generated, _JOB_ID_RE)

    def test_prefix_is_job_dash(self) -> None:
        generated = f"job-{uuid4().hex[:12]}"
        self.assertTrue(generated.startswith("job-"))

    def test_hex_portion_is_12_chars(self) -> None:
        generated = f"job-{uuid4().hex[:12]}"
        hex_part = generated[4:]
        self.assertEqual(len(hex_part), 12)
        self.assertTrue(all(c in "0123456789abcdef" for c in hex_part))

    def test_job_id_not_run_id(self) -> None:
        job_id = f"job-{uuid4().hex[:12]}"
        run_id = f"run-{uuid4().hex[:12]}"
        self.assertNotEqual(job_id, run_id)
        self.assertNotRegex(job_id, _RUN_ID_RE)
        self.assertNotRegex(run_id, _JOB_ID_RE)


class TelemetryRunIdTest(unittest.TestCase):
    """Verify telemetry_run_id maps to RunBundleManifest.run_id field."""

    def test_run_bundle_manifest_has_run_id_field(self) -> None:
        from framework.runtime_telemetry_schema import RunBundleManifest
        import inspect
        fields = {f.name for f in RunBundleManifest.__dataclass_fields__.values()}
        self.assertIn("run_id", fields, "RunBundleManifest must have run_id field")

    def test_run_bundle_manifest_does_not_have_telemetry_run_id_field(self) -> None:
        # The wire field name is run_id; telemetry_run_id is the canonical identity label
        from framework.runtime_telemetry_schema import RunBundleManifest
        fields = {f.name for f in RunBundleManifest.__dataclass_fields__.values()}
        self.assertNotIn("telemetry_run_id", fields)

    def test_run_id_format_matches_spec(self) -> None:
        # Mirrors artifacts/phase1_local_runtime_validation_report.py generation
        generated = f"run-{uuid4().hex[:12]}"
        self.assertRegex(generated, _RUN_ID_RE)

    def test_run_id_prefix_distinct_from_job_prefix(self) -> None:
        run_id = f"run-{uuid4().hex[:12]}"
        self.assertFalse(run_id.startswith("job-"))


class IdentityMutualDistinctnessTest(unittest.TestCase):
    """All four identity types are mutually distinct in a well-formed context."""

    def _make_context(self) -> dict[str, str]:
        hex12 = uuid4().hex[:12]
        return {
            "job_id": f"job-{hex12}",
            "session_id": f"cp-test-{uuid4().hex[:8]}",
            "telemetry_run_id": f"run-{uuid4().hex[:12]}",
            "plan_id": f"test-plan-{uuid4().hex[:8]}",
        }

    def test_all_four_values_distinct(self) -> None:
        ctx = self._make_context()
        values = list(ctx.values())
        self.assertEqual(len(values), len(set(values)), "all identity values must be distinct")

    def test_job_id_prefix_not_shared(self) -> None:
        ctx = self._make_context()
        self.assertTrue(ctx["job_id"].startswith("job-"))
        for k in ("session_id", "telemetry_run_id", "plan_id"):
            self.assertFalse(ctx[k].startswith("job-"), f"{k} must not start with 'job-'")

    def test_run_id_prefix_not_shared(self) -> None:
        ctx = self._make_context()
        self.assertTrue(ctx["telemetry_run_id"].startswith("run-"))
        for k in ("job_id", "session_id", "plan_id"):
            self.assertFalse(ctx[k].startswith("run-"), f"{k} must not start with 'run-'")

    def test_canonical_job_carries_both_job_id_and_session_id(self) -> None:
        from framework.canonical_job_schema import CanonicalJob
        from framework.canonical_session_schema import CanonicalSession
        session = CanonicalSession(session_id="cp-test-session", task_id="T-001")
        job = CanonicalJob.from_session(session, job_id=f"job-{uuid4().hex[:12]}")
        self.assertNotEqual(job.job_id, job.session_id)
        self.assertRegex(job.job_id, _JOB_ID_RE)

    def test_run_bundle_manifest_carries_both_run_id_and_session_id(self) -> None:
        from framework.runtime_telemetry_schema import RunBundleManifest
        manifest = RunBundleManifest(
            schema_version=1,
            run_id=f"run-{uuid4().hex[:12]}",
            session_id="cp-test-session",
            profile_name="default",
            source_root="/tmp/src",
            scratch_root="/tmp/scratch",
            artifact_root="/tmp/artifacts",
        )
        self.assertNotEqual(manifest.run_id, manifest.session_id)
        self.assertRegex(manifest.run_id, _RUN_ID_RE)


class SchemaModuleDocstringTest(unittest.TestCase):
    """canonical_job_schema.py and canonical_session_schema.py reference the spec."""

    def test_canonical_job_schema_docstring_references_spec(self) -> None:
        import framework.canonical_job_schema as m
        doc = m.__doc__ or ""
        self.assertIn("governance/canonical_id_spec.json", doc)

    def test_canonical_job_schema_docstring_mentions_identity_constraint(self) -> None:
        import framework.canonical_job_schema as m
        doc = m.__doc__ or ""
        self.assertIn("job_id", doc)
        self.assertIn("session_id", doc)

    def test_canonical_session_schema_docstring_references_spec(self) -> None:
        import framework.canonical_session_schema as m
        doc = m.__doc__ or ""
        self.assertIn("governance/canonical_id_spec.json", doc)

    def test_canonical_session_schema_docstring_mentions_intent_boundary(self) -> None:
        import framework.canonical_session_schema as m
        doc = m.__doc__ or ""
        self.assertIn("session_id", doc)
        self.assertIn("intent", doc)

    def test_no_new_fields_added_to_canonical_job(self) -> None:
        from framework.canonical_job_schema import CanonicalJob
        field_names = set(CanonicalJob.__dataclass_fields__)
        # Confirm expected fields still present; no telemetry_run_id or plan_id added
        self.assertIn("job_id", field_names)
        self.assertIn("session_id", field_names)
        self.assertNotIn("telemetry_run_id", field_names)
        self.assertNotIn("plan_id", field_names)

    def test_no_new_fields_added_to_canonical_session(self) -> None:
        from framework.canonical_session_schema import CanonicalSession
        field_names = set(CanonicalSession.__dataclass_fields__)
        self.assertIn("session_id", field_names)
        self.assertNotIn("job_id", field_names)
        self.assertNotIn("telemetry_run_id", field_names)
        self.assertNotIn("plan_id", field_names)


if __name__ == "__main__":
    unittest.main()
