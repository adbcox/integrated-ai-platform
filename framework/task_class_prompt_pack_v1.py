"""Task-class prompt pack surface for Phase 4 self-sufficiency uplift (P4-01)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass(frozen=True)
class PromptPackEntryV1:
    task_class: str
    system_guidance: str
    execution_guidance: str
    validation_guidance: str

    def to_dict(self) -> dict:
        return {
            "task_class": self.task_class,
            "system_guidance": self.system_guidance,
            "execution_guidance": self.execution_guidance,
            "validation_guidance": self.validation_guidance,
        }


_DEFAULT_ENTRIES: List[PromptPackEntryV1] = [
    PromptPackEntryV1(
        task_class="bug_fix",
        system_guidance=(
            "You are fixing a specific, scoped bug. Read the failing test or error trace first. "
            "Make the minimum change required. Do not refactor surrounding code."
        ),
        execution_guidance=(
            "1. Read the target file(s). "
            "2. Identify the exact faulty line or logic path. "
            "3. Apply the minimal correction. "
            "4. Verify the fix does not break adjacent logic."
        ),
        validation_guidance=(
            "Run the affected test suite. Confirm the previously failing assertion now passes. "
            "Confirm no pre-existing passing tests regress."
        ),
    ),
    PromptPackEntryV1(
        task_class="narrow_feature",
        system_guidance=(
            "You are adding a narrow, bounded feature to an existing module. "
            "Do not restructure existing interfaces. Add only what the task specifies."
        ),
        execution_guidance=(
            "1. Read the target module to understand its interface. "
            "2. Identify the insertion point. "
            "3. Implement only the requested feature. "
            "4. Leave all existing behavior unchanged."
        ),
        validation_guidance=(
            "Run the full test suite for the target module. "
            "Add at minimum one test covering the new feature path."
        ),
    ),
    PromptPackEntryV1(
        task_class="reporting_helper",
        system_guidance=(
            "You are producing a structured reporting helper. "
            "Output must be serializable (JSON/dict). Do not call external services."
        ),
        execution_guidance=(
            "1. Define the required output fields. "
            "2. Implement a to_dict() method. "
            "3. Do not print or log inside library code; return structured data."
        ),
        validation_guidance=(
            "Verify to_dict() produces all required keys. "
            "Verify the output is JSON-serializable."
        ),
    ),
    PromptPackEntryV1(
        task_class="test_addition",
        system_guidance=(
            "You are adding tests to an existing test file or creating a new seam test. "
            "Tests must be deterministic and offline-safe."
        ),
        execution_guidance=(
            "1. Read the module under test. "
            "2. Identify untested or under-tested paths. "
            "3. Write focused, isolated test functions. "
            "4. Use only stdlib or existing project dependencies."
        ),
        validation_guidance=(
            "Run pytest on the new test file. All new tests must pass. "
            "No existing tests may regress."
        ),
    ),
]

_ENTRY_MAP: Dict[str, PromptPackEntryV1] = {e.task_class: e for e in _DEFAULT_ENTRIES}


class TaskClassPromptPackV1:
    def __init__(self, entries: Optional[List[PromptPackEntryV1]] = None) -> None:
        if entries is not None:
            self._entries = {e.task_class: e for e in entries}
        else:
            self._entries = dict(_ENTRY_MAP)

    def get(self, task_class: str) -> Optional[PromptPackEntryV1]:
        return self._entries.get(task_class)

    def list_classes(self) -> List[str]:
        return sorted(self._entries.keys())

    def all_entries(self) -> List[PromptPackEntryV1]:
        return [self._entries[k] for k in sorted(self._entries)]

    def register(self, entry: PromptPackEntryV1) -> None:
        self._entries[entry.task_class] = entry
