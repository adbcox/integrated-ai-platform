"""Tests for framework.critique_injector — critique injection + retry guidance seam."""
import pytest
from pathlib import Path

from framework.critique_injector import CritiqueResult, build_critique, render_retry_prompt
from framework.local_memory_store import LocalMemoryStore


@pytest.fixture
def store(tmp_path):
    return LocalMemoryStore(memory_dir=tmp_path / "memory")


def test_import_ok():
    from framework.critique_injector import build_critique, render_retry_prompt  # noqa: F401


def test_build_critique_returns_critique_result(store):
    result = build_critique(
        task_kind="text_replacement",
        last_error="old_string not found in file",
        memory_store=store,
    )
    assert isinstance(result, CritiqueResult)


def test_build_critique_classifies_old_string_not_found(store):
    result = build_critique(
        task_kind="text_replacement",
        last_error="old_string not found in file",
        memory_store=store,
    )
    assert result.error_type == "old_string_not_found"


def test_build_critique_classifies_test_failed(store):
    result = build_critique(
        task_kind="bug_fix",
        last_error="test failed exit code 1",
        memory_store=store,
    )
    assert result.error_type == "test_failed"


def test_build_critique_classifies_permission(store):
    result = build_critique(
        task_kind="text_replacement",
        last_error="path outside writable roots permission denied",
        memory_store=store,
    )
    assert result.error_type == "permission_denied"


def test_build_critique_retry_advised_with_low_failure_rate(store):
    store.record_success(task_kind="text_replacement", target_file="a.py", old_string="x", new_string="y")
    result = build_critique(
        task_kind="text_replacement",
        last_error="old_string not found in file",
        memory_store=store,
    )
    assert result.retry_advised is True


def test_build_critique_retry_not_advised_with_high_failure_rate(store):
    for _ in range(5):
        store.record_failure(task_kind="bug_fix", target_file="f.py", old_string="x", error="test failed")
    result = build_critique(
        task_kind="bug_fix",
        last_error="test failed",
        memory_store=store,
        max_failure_rate_for_retry=0.5,
    )
    assert result.retry_advised is False


def test_critique_text_contains_guidance_for_error_type(store):
    result = build_critique(
        task_kind="text_replacement",
        last_error="old_string not found in file",
        memory_store=store,
    )
    assert "whitespace" in result.critique_text.lower() or "exact" in result.critique_text.lower()


def test_critique_text_contains_test_guidance_for_test_failed(store):
    result = build_critique(
        task_kind="bug_fix",
        last_error="test failed",
        memory_store=store,
    )
    assert "invariant" in result.critique_text.lower() or "minimal" in result.critique_text.lower()


def test_as_extra_instructions_contains_error_type(store):
    result = build_critique(
        task_kind="text_replacement",
        last_error="old_string not found in file",
        memory_store=store,
    )
    instructions = result.as_extra_instructions()
    assert "old_string_not_found" in instructions


def test_as_extra_instructions_blocked_when_retry_not_advised(store):
    for _ in range(5):
        store.record_failure(task_kind="narrow_test_update", target_file="f.py", old_string="x", error="test failed")
    result = build_critique(
        task_kind="narrow_test_update",
        last_error="test failed",
        memory_store=store,
        max_failure_rate_for_retry=0.5,
    )
    instructions = result.as_extra_instructions()
    assert "RETRY BLOCKED" in instructions


def test_pattern_count_reflects_stored_failures(store):
    store.record_failure(task_kind="text_replacement", target_file="a.py", old_string="x", error="old_string not found in file")
    store.record_failure(task_kind="text_replacement", target_file="b.py", old_string="y", error="old_string not found in file")
    result = build_critique(
        task_kind="text_replacement",
        last_error="old_string not found in file",
        memory_store=store,
    )
    assert result.pattern_count == 2


def test_build_critique_with_explicit_error_type(store):
    result = build_critique(
        task_kind="metadata_addition",
        last_error=None,
        last_error_type="permission_denied",
        memory_store=store,
    )
    assert result.error_type == "permission_denied"


def test_render_retry_prompt_returns_string(store):
    prompt = render_retry_prompt(
        "text_replacement",
        target_file="framework/foo.py",
        file_content="VERSION = '1.0'\n",
        old_string="VERSION = '1.0'",
        new_string_hint="VERSION = '2.0'",
        last_error="old_string not found in file",
        memory_store=store,
    )
    assert isinstance(prompt, str)
    assert len(prompt) > 100


def test_render_retry_prompt_contains_critique(store):
    prompt = render_retry_prompt(
        "bug_fix",
        target_file="framework/foo.py",
        file_content="return None\n",
        old_string="return None",
        last_error="test failed exit code 1",
        memory_store=store,
    )
    assert "RETRY GUIDANCE" in prompt or "minimal" in prompt.lower()


def test_render_retry_prompt_falls_back_for_unsupported_task_class(store):
    prompt = render_retry_prompt(
        "unsupported_task_class_xyz",
        target_file="f.py",
        file_content="x = 1\n",
        old_string="x = 1",
        last_error="err",
        memory_store=store,
    )
    assert isinstance(prompt, str)
    assert len(prompt) > 50


def test_render_retry_prompt_includes_file_content(store):
    content = "MY_UNIQUE_SENTINEL_CONTENT = True\n"
    prompt = render_retry_prompt(
        "text_replacement",
        target_file="f.py",
        file_content=content,
        old_string="MY_UNIQUE_SENTINEL_CONTENT = True",
        last_error="old_string not found in file",
        memory_store=store,
    )
    assert "MY_UNIQUE_SENTINEL_CONTENT" in prompt


def test_build_critique_no_memory_store_uses_default():
    # Uses default memory dir — should not raise
    result = build_critique(
        task_kind="text_replacement",
        last_error="old_string not found in file",
    )
    assert isinstance(result, CritiqueResult)
