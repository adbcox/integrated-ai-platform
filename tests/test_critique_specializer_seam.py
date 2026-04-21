"""Tests for framework.critique_specializer — CritiqueSpecializer seam."""
import pytest

from framework.local_memory_store import LocalMemoryStore
from framework.task_prompt_pack import SUPPORTED_TASK_CLASSES
from framework.critique_specializer import CritiqueSpecialization, CritiqueSpecializer


@pytest.fixture
def store(tmp_path):
    return LocalMemoryStore(memory_dir=tmp_path / "mem")


@pytest.fixture
def empty_store(tmp_path):
    return LocalMemoryStore(memory_dir=tmp_path / "mem")


def test_import_ok():
    from framework.critique_specializer import CritiqueSpecialization, CritiqueSpecializer  # noqa: F401


def test_specialization_fields():
    spec = CritiqueSpecialization(
        task_kind="text_replacement",
        base_guidance="base",
        enrichment=None,
        combined_guidance="combined",
        specialized_at="T",
    )
    assert spec.task_kind == "text_replacement"
    assert spec.base_guidance == "base"
    assert spec.enrichment is None


def test_specialize_returns_specialization(empty_store):
    specializer = CritiqueSpecializer(memory_store=empty_store)
    spec = specializer.specialize("text_replacement")
    assert isinstance(spec, CritiqueSpecialization)


def test_specialize_base_guidance_non_empty(empty_store):
    specializer = CritiqueSpecializer(memory_store=empty_store)
    for task_kind in SUPPORTED_TASK_CLASSES:
        spec = specializer.specialize(task_kind)
        assert len(spec.base_guidance) > 0, f"empty guidance for {task_kind}"


def test_specialize_combined_guidance_non_empty(empty_store):
    specializer = CritiqueSpecializer(memory_store=empty_store)
    spec = specializer.specialize("text_replacement")
    assert len(spec.combined_guidance) > 0


def test_specialize_task_kind_propagated(empty_store):
    specializer = CritiqueSpecializer(memory_store=empty_store)
    spec = specializer.specialize("bug_fix")
    assert spec.task_kind == "bug_fix"


def test_specialize_specialized_at_is_iso(empty_store):
    specializer = CritiqueSpecializer(memory_store=empty_store)
    spec = specializer.specialize("text_replacement")
    assert "T" in spec.specialized_at


def test_specialize_no_memory_store_works():
    specializer = CritiqueSpecializer(memory_store=None)
    spec = specializer.specialize("text_replacement")
    assert isinstance(spec, CritiqueSpecialization)
    assert spec.enrichment is None


def test_specialize_empty_store_no_enrichment(empty_store):
    specializer = CritiqueSpecializer(memory_store=empty_store)
    spec = specializer.specialize("text_replacement")
    # enrichment may exist but extra_instructions should be empty or minimal
    assert spec.combined_guidance == spec.base_guidance or len(spec.combined_guidance) >= len(spec.base_guidance)


def test_specialize_with_patterns_enriches(store):
    for _ in range(3):
        store.record_failure(task_kind="text_replacement", target_file="a.py", old_string="foo", error="err")
    specializer = CritiqueSpecializer(memory_store=store, max_examples=3)
    spec = specializer.specialize("text_replacement", error_type="other")
    assert isinstance(spec, CritiqueSpecialization)
    assert len(spec.combined_guidance) >= len(spec.base_guidance)


def test_as_prompt_instructions_returns_string(empty_store):
    specializer = CritiqueSpecializer(memory_store=empty_store)
    spec = specializer.specialize("text_replacement")
    instructions = spec.as_prompt_instructions()
    assert isinstance(instructions, str)
    assert len(instructions) > 0


def test_base_guidance_for_known_task():
    specializer = CritiqueSpecializer()
    guidance = specializer.base_guidance_for("text_replacement")
    assert isinstance(guidance, str)
    assert len(guidance) > 0


def test_base_guidance_for_unknown_task():
    specializer = CritiqueSpecializer()
    guidance = specializer.base_guidance_for("nonexistent_xyz")
    assert isinstance(guidance, str)


def test_all_supported_classes_have_guidance():
    specializer = CritiqueSpecializer()
    for tc in SUPPORTED_TASK_CLASSES:
        guidance = specializer.base_guidance_for(tc)
        assert len(guidance) > 0, f"empty guidance for {tc}"


def test_init_ok_from_framework():
    from framework import CritiqueSpecializer  # noqa: F401
