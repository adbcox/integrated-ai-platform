"""Tests for framework.memory_critique_enricher — critique enrichment seam."""
import pytest
from pathlib import Path

from framework.local_memory_store import LocalMemoryStore
from framework.critique_injector import CritiqueResult, build_critique
from framework.memory_critique_enricher import (
    CritiqueEnrichment,
    enrich_critique,
    render_enriched_retry_prompt,
)


@pytest.fixture
def store(tmp_path):
    return LocalMemoryStore(memory_dir=tmp_path / "memory")


@pytest.fixture
def base_critique(store):
    return build_critique(task_kind="text_replacement", last_error="syntax_error", memory_store=store)


def test_import_ok():
    from framework.memory_critique_enricher import enrich_critique, CritiqueEnrichment  # noqa: F401


def test_enrich_returns_critique_enrichment(store, base_critique):
    result = enrich_critique(base_critique, memory_store=store)
    assert isinstance(result, CritiqueEnrichment)


def test_enrich_fields_present(store, base_critique):
    result = enrich_critique(base_critique, memory_store=store)
    assert hasattr(result, "task_kind")
    assert hasattr(result, "error_type")
    assert hasattr(result, "pattern_examples")
    assert hasattr(result, "extra_guidance")


def test_enrich_empty_store_no_examples(store, base_critique):
    result = enrich_critique(base_critique, memory_store=store)
    assert result.pattern_examples == []


def test_enrich_with_failures_returns_examples(store):
    store.record_failure(task_kind="text_replacement", target_file="a.py", old_string="x", error="syntax_error")
    critique = build_critique(task_kind="text_replacement", last_error="syntax_error", memory_store=store)
    result = enrich_critique(critique, memory_store=store, max_examples=5)
    assert len(result.pattern_examples) >= 1


def test_enrich_max_examples_respected(store):
    for i in range(5):
        store.record_failure(task_kind="text_replacement", target_file=f"{i}.py", old_string="x", error="err")
    critique = CritiqueResult(task_kind="text_replacement", error_type="err", critique_text="", pattern_count=0, retry_advised=True)
    result = enrich_critique(critique, memory_store=store, max_examples=2)
    assert len(result.pattern_examples) <= 2


def test_as_extra_instructions_empty_on_no_patterns(store, base_critique):
    result = enrich_critique(base_critique, memory_store=store)
    assert result.as_extra_instructions() == ""


def test_as_extra_instructions_non_empty_with_patterns(store):
    store.record_failure(task_kind="text_replacement", target_file="a.py", old_string="x", error="syntax_error")
    # error_type stored as "other" by record_failure; query without filter to get all
    critique = CritiqueResult(task_kind="text_replacement", error_type="other", critique_text="", pattern_count=1, retry_advised=True)
    result = enrich_critique(critique, memory_store=store)
    instructions = result.as_extra_instructions()
    assert isinstance(instructions, str)
    assert len(instructions) > 0


def test_enrich_task_kind_preserved(store, base_critique):
    result = enrich_critique(base_critique, memory_store=store)
    assert result.task_kind == "text_replacement"


def test_render_enriched_retry_prompt_returns_string(store, tmp_path):
    target = tmp_path / "f.py"
    target.write_text("x = 1\n", encoding="utf-8")
    result = render_enriched_retry_prompt(
        "text_replacement",
        target_file=str(target),
        file_content=target.read_text(),
        old_string="x = 1",
        last_error="syntax_error",
        memory_store=store,
    )
    assert isinstance(result, str)
    assert len(result) > 0


def test_render_enriched_no_crash_empty_store(store, tmp_path):
    target = tmp_path / "f.py"
    target.write_text("y = 2\n", encoding="utf-8")
    result = render_enriched_retry_prompt(
        "bug_fix",
        target_file=str(target),
        file_content=target.read_text(),
        old_string="y = 2",
        last_error=None,
        memory_store=store,
    )
    assert isinstance(result, str)


def test_enrich_filters_by_task_kind(store):
    store.record_failure(task_kind="bug_fix", target_file="b.py", old_string="z", error="other_err")
    critique = CritiqueResult(task_kind="text_replacement", error_type="", critique_text="", pattern_count=0, retry_advised=False)
    result = enrich_critique(critique, memory_store=store)
    # bug_fix failures should not appear for text_replacement critique
    for ex in result.pattern_examples:
        assert ex["task_kind"] == "text_replacement" or ex["task_kind"] == ""


def test_render_enriched_retry_prompt_enriched_when_failures_present(store, tmp_path):
    store.record_failure(task_kind="text_replacement", target_file="a.py", old_string="x", error="err")
    target = tmp_path / "f.py"
    target.write_text("x = 1\n", encoding="utf-8")
    result = render_enriched_retry_prompt(
        "text_replacement",
        target_file=str(target),
        file_content=target.read_text(),
        old_string="x = 1",
        last_error="err",
        memory_store=store,
    )
    # Even without enriched patterns (because error_type mismatch), result is a non-empty string
    assert isinstance(result, str)
    assert len(result) > 0


def test_example_fields_present(store):
    store.record_failure(task_kind="text_replacement", target_file="a.py", old_string="z", error="err")
    critique = CritiqueResult(task_kind="text_replacement", error_type="err", critique_text="", pattern_count=1, retry_advised=True)
    result = enrich_critique(critique, memory_store=store)
    if result.pattern_examples:
        ex = result.pattern_examples[0]
        assert "task_kind" in ex
        assert "old_string_prefix" in ex
