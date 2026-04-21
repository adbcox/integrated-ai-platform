"""Conformance tests for canonical typed Action→Observation tool contract (RUNTIME-CONTRACT-A1-TOOL-SEAM-1).

Covers:
- all 9 tools registered
- representative Action constructible
- representative Observation constructible
- all Action types constructible
- all Observation types constructible
- Action types frozen
- Observation types frozen
- registry returns correct entry
- registry unknown returns None
- action/observation maps have matching tool names
- spec parses and covers all 9 tools
- spec snapshot artifact written and valid
"""

from __future__ import annotations

import json
import sys
import unittest
from dataclasses import FrozenInstanceError
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.tool_schema import (
    TOOL_ACTION_TYPES,
    TOOL_OBSERVATION_TYPES,
    ApplyPatchAction,
    ApplyPatchObservation,
    GitDiffAction,
    GitDiffObservation,
    ListDirAction,
    ListDirObservation,
    PublishArtifactAction,
    PublishArtifactObservation,
    ReadFileAction,
    ReadFileObservation,
    RepoMapAction,
    RepoMapObservation,
    RunCommandAction,
    RunCommandObservation,
    RunTestsAction,
    RunTestsObservation,
    SearchAction,
    SearchObservation,
    ToolAction,
    ToolObservation,
)
from framework.tool_registry import DEFAULT_REGISTRY, ToolContractEntry, ToolRegistry

SPEC_PATH = REPO_ROOT / "governance" / "tool_contract_spec.json"
SNAPSHOT_DIR = REPO_ROOT / "artifacts" / "framework" / "tool_contract"
SNAPSHOT_PATH = SNAPSHOT_DIR / "spec_snapshot.json"

_NINE_TOOL_NAMES = {
    "read_file", "search", "list_dir", "repo_map", "apply_patch",
    "git_diff", "run_command", "run_tests", "publish_artifact",
}


class RegistrationTest(unittest.TestCase):
    """All 9 tools must be registered in DEFAULT_REGISTRY."""

    def test_registry_has_nine_tools(self) -> None:
        self.assertEqual(len(DEFAULT_REGISTRY), 9)

    def test_all_nine_names_registered(self) -> None:
        registered = set(DEFAULT_REGISTRY.list_tools())
        missing = _NINE_TOOL_NAMES - registered
        self.assertEqual(missing, set(), f"missing tools: {missing}")

    def test_list_tools_sorted(self) -> None:
        names = DEFAULT_REGISTRY.list_tools()
        self.assertEqual(names, sorted(names))

    def test_registry_unknown_returns_none(self) -> None:
        self.assertIsNone(DEFAULT_REGISTRY.get("nonexistent_tool"))

    def test_registry_returns_correct_entry(self) -> None:
        entry = DEFAULT_REGISTRY.get("read_file")
        self.assertIsNotNone(entry)
        self.assertEqual(entry.name, "read_file")
        self.assertIs(entry.action_type, ReadFileAction)
        self.assertIs(entry.observation_type, ReadFileObservation)

    def test_all_entries_are_tool_contract_entry(self) -> None:
        for name in _NINE_TOOL_NAMES:
            entry = DEFAULT_REGISTRY.get(name)
            self.assertIsInstance(entry, ToolContractEntry, f"{name} entry wrong type")

    def test_register_and_get_roundtrip(self) -> None:
        reg = ToolRegistry()
        entry = ToolContractEntry(
            name="test_tool",
            action_type=ReadFileAction,
            observation_type=ReadFileObservation,
        )
        reg.register(entry)
        self.assertIs(reg.get("test_tool"), entry)
        self.assertEqual(len(reg), 1)


class RepresentativeConstructionTest(unittest.TestCase):
    """Representative Action and Observation types must be constructible."""

    def test_read_file_action_constructible(self) -> None:
        a = ReadFileAction(path="src/main.py")
        self.assertEqual(a.path, "src/main.py")

    def test_read_file_observation_constructible(self) -> None:
        o = ReadFileObservation(path="src/main.py", content="print('hello')")
        self.assertEqual(o.content, "print('hello')")
        self.assertIsNone(o.error)

    def test_run_command_action_constructible(self) -> None:
        a = RunCommandAction(command="make check")
        self.assertEqual(a.command, "make check")
        self.assertEqual(a.cwd, ".")
        self.assertEqual(a.timeout_seconds, 30)

    def test_apply_patch_action_constructible(self) -> None:
        a = ApplyPatchAction(path="foo.py", old_string="old", new_string="new")
        self.assertEqual(a.path, "foo.py")


class AllActionTypesConstructibleTest(unittest.TestCase):
    """All 9 Action types must be constructible with minimal args."""

    def test_read_file_action(self) -> None:
        self.assertIsInstance(ReadFileAction(path="x"), ReadFileAction)

    def test_search_action(self) -> None:
        self.assertIsInstance(SearchAction(query="def main"), SearchAction)

    def test_list_dir_action(self) -> None:
        self.assertIsInstance(ListDirAction(path="."), ListDirAction)

    def test_repo_map_action(self) -> None:
        self.assertIsInstance(RepoMapAction(), RepoMapAction)

    def test_apply_patch_action(self) -> None:
        self.assertIsInstance(ApplyPatchAction(path="x", old_string="", new_string=""), ApplyPatchAction)

    def test_git_diff_action(self) -> None:
        self.assertIsInstance(GitDiffAction(), GitDiffAction)

    def test_run_command_action(self) -> None:
        self.assertIsInstance(RunCommandAction(command="echo"), RunCommandAction)

    def test_run_tests_action(self) -> None:
        self.assertIsInstance(RunTestsAction(), RunTestsAction)

    def test_publish_artifact_action(self) -> None:
        self.assertIsInstance(
            PublishArtifactAction(artifact_path="a.json", destination="store/a.json"),
            PublishArtifactAction,
        )


class AllObservationTypesConstructibleTest(unittest.TestCase):
    """All 9 Observation types must be constructible with minimal args."""

    def test_read_file_observation(self) -> None:
        self.assertIsInstance(ReadFileObservation(path="x", content=""), ReadFileObservation)

    def test_search_observation(self) -> None:
        self.assertIsInstance(SearchObservation(query="q"), SearchObservation)

    def test_list_dir_observation(self) -> None:
        self.assertIsInstance(ListDirObservation(path="."), ListDirObservation)

    def test_repo_map_observation(self) -> None:
        self.assertIsInstance(RepoMapObservation(root="."), RepoMapObservation)

    def test_apply_patch_observation(self) -> None:
        self.assertIsInstance(ApplyPatchObservation(path="x", applied=True), ApplyPatchObservation)

    def test_git_diff_observation(self) -> None:
        self.assertIsInstance(GitDiffObservation(diff=""), GitDiffObservation)

    def test_run_command_observation(self) -> None:
        self.assertIsInstance(
            RunCommandObservation(stdout="", stderr="", exit_code=0),
            RunCommandObservation,
        )

    def test_run_tests_observation(self) -> None:
        self.assertIsInstance(
            RunTestsObservation(stdout="", stderr="", exit_code=0, passed=1, failed=0, skipped=0),
            RunTestsObservation,
        )

    def test_publish_artifact_observation(self) -> None:
        self.assertIsInstance(
            PublishArtifactObservation(artifact_path="a", destination="b", published=True),
            PublishArtifactObservation,
        )


class FrozenTest(unittest.TestCase):
    """Action and Observation types must be immutable (frozen)."""

    def test_action_is_frozen(self) -> None:
        a = ReadFileAction(path="x")
        with self.assertRaises(FrozenInstanceError):
            a.path = "y"  # type: ignore[misc]

    def test_observation_is_frozen(self) -> None:
        o = ReadFileObservation(path="x", content="c")
        with self.assertRaises(FrozenInstanceError):
            o.content = "d"  # type: ignore[misc]

    def test_run_command_action_frozen(self) -> None:
        a = RunCommandAction(command="make")
        with self.assertRaises(FrozenInstanceError):
            a.command = "ls"  # type: ignore[misc]

    def test_apply_patch_observation_frozen(self) -> None:
        o = ApplyPatchObservation(path="f", applied=False)
        with self.assertRaises(FrozenInstanceError):
            o.applied = True  # type: ignore[misc]

    def test_base_action_is_frozen(self) -> None:
        self.assertTrue(ToolAction.__dataclass_params__.frozen)

    def test_base_observation_is_frozen(self) -> None:
        self.assertTrue(ToolObservation.__dataclass_params__.frozen)


class LookupDictTest(unittest.TestCase):
    """TOOL_ACTION_TYPES and TOOL_OBSERVATION_TYPES must cover matching tool names."""

    def test_action_map_has_nine_entries(self) -> None:
        self.assertEqual(len(TOOL_ACTION_TYPES), 9)

    def test_observation_map_has_nine_entries(self) -> None:
        self.assertEqual(len(TOOL_OBSERVATION_TYPES), 9)

    def test_action_and_observation_keys_match(self) -> None:
        self.assertEqual(set(TOOL_ACTION_TYPES.keys()), set(TOOL_OBSERVATION_TYPES.keys()))

    def test_action_map_covers_all_nine(self) -> None:
        missing = _NINE_TOOL_NAMES - set(TOOL_ACTION_TYPES.keys())
        self.assertEqual(missing, set(), f"action map missing: {missing}")

    def test_observation_map_covers_all_nine(self) -> None:
        missing = _NINE_TOOL_NAMES - set(TOOL_OBSERVATION_TYPES.keys())
        self.assertEqual(missing, set(), f"observation map missing: {missing}")

    def test_action_types_are_subclasses_of_tool_action(self) -> None:
        for name, cls in TOOL_ACTION_TYPES.items():
            self.assertTrue(
                issubclass(cls, ToolAction),
                f"{name}: {cls} is not a subclass of ToolAction",
            )

    def test_observation_types_are_subclasses_of_tool_observation(self) -> None:
        for name, cls in TOOL_OBSERVATION_TYPES.items():
            self.assertTrue(
                issubclass(cls, ToolObservation),
                f"{name}: {cls} is not a subclass of ToolObservation",
            )


class SpecFileTest(unittest.TestCase):
    """governance/tool_contract_spec.json must parse and cover all 9 tools."""

    def setUp(self) -> None:
        self.spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))

    def test_spec_parses(self) -> None:
        self.assertIsInstance(self.spec, dict)

    def test_spec_has_schema_version(self) -> None:
        self.assertIn("schema_version", self.spec)
        self.assertEqual(self.spec["schema_version"], "1.0.0")

    def test_spec_has_authority(self) -> None:
        self.assertIn("authority", self.spec)

    def test_spec_has_tools_array(self) -> None:
        self.assertIn("tools", self.spec)
        self.assertIsInstance(self.spec["tools"], list)

    def test_spec_tools_length_nine(self) -> None:
        self.assertEqual(len(self.spec["tools"]), 9)

    def test_spec_covers_all_nine_tool_names(self) -> None:
        names = {t["name"] for t in self.spec["tools"]}
        missing = _NINE_TOOL_NAMES - names
        self.assertEqual(missing, set(), f"spec missing tools: {missing}")

    def test_each_tool_has_action_type(self) -> None:
        for tool in self.spec["tools"]:
            self.assertIn("action_type", tool, f"tool {tool['name']} missing action_type")

    def test_each_tool_has_observation_type(self) -> None:
        for tool in self.spec["tools"]:
            self.assertIn("observation_type", tool, f"tool {tool['name']} missing observation_type")

    def test_each_tool_has_action_fields(self) -> None:
        for tool in self.spec["tools"]:
            self.assertIn("action_fields", tool, f"tool {tool['name']} missing action_fields")

    def test_each_tool_has_observation_fields(self) -> None:
        for tool in self.spec["tools"]:
            self.assertIn("observation_fields", tool, f"tool {tool['name']} missing observation_fields")

    def test_spec_has_description(self) -> None:
        self.assertIn("description", self.spec)

    def test_spec_has_generated_at(self) -> None:
        self.assertIn("generated_at", self.spec)


class SpecSnapshotArtifactTest(unittest.TestCase):
    """Test writes spec_snapshot.json to artifacts/framework/tool_contract/."""

    def test_snapshot_artifact_written_and_valid(self) -> None:
        SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
        spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
        snapshot = {
            "schema_version": spec["schema_version"],
            "tool_names": sorted(t["name"] for t in spec["tools"]),
            "tool_count": len(spec["tools"]),
            "action_types": {t["name"]: t["action_type"] for t in spec["tools"]},
            "observation_types": {t["name"]: t["observation_type"] for t in spec["tools"]},
            "registry_tool_names": DEFAULT_REGISTRY.list_tools(),
        }
        SNAPSHOT_PATH.write_text(
            json.dumps(snapshot, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        self.assertTrue(SNAPSHOT_PATH.exists())
        parsed = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
        self.assertEqual(parsed["tool_count"], 9)
        self.assertEqual(set(parsed["tool_names"]), _NINE_TOOL_NAMES)


if __name__ == "__main__":
    unittest.main()
