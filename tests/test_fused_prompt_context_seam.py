"""Conformance tests for framework/fused_prompt_context.py (LARAC2-PROMPT-CONTEXT-FUSION-SEAM-1)."""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.fused_prompt_context import FusedPromptContext, build_fused_prompt
from framework.hybrid_inspect_context import HybridInspectContext


def _ctx(cache_snippet="", search_snippet="", pattern_hints=None, context_sources=None):
    return HybridInspectContext(
        query="q",
        cache_snippet=cache_snippet,
        pattern_hints=pattern_hints or [],
        search_snippet=search_snippet,
        context_sources=context_sources or [],
        error_notes=[],
    )


# --- import and type ---

def test_import_build_fused_prompt():
    assert callable(build_fused_prompt)


def test_returns_fused_prompt_context():
    r = build_fused_prompt("text_replacement", target_file="f.py", file_content="x=1")
    assert isinstance(r, FusedPromptContext)


# --- fields ---

def test_result_fields_present():
    r = build_fused_prompt("text_replacement", target_file="f.py", file_content="x=1")
    assert hasattr(r, "task_class")
    assert hasattr(r, "target_file")
    assert hasattr(r, "prompt")
    assert hasattr(r, "context_sources")
    assert hasattr(r, "fallback_used")


# --- supported task class ---

def test_supported_task_class_no_fallback():
    r = build_fused_prompt("text_replacement", target_file="f.py", file_content="x=1")
    assert r.fallback_used is False
    assert isinstance(r.prompt, str)
    assert len(r.prompt) > 0


def test_unsupported_task_class_fallback():
    r = build_fused_prompt("unknown_task_class", target_file="f.py", file_content="x=1")
    assert r.fallback_used is True


def test_unsupported_task_class_prompt_non_empty():
    r = build_fused_prompt("unknown_task_class", target_file="f.py", file_content="x=1")
    assert len(r.prompt) > 0


# --- hybrid context injection ---

def test_context_snippet_injected():
    ctx = _ctx(cache_snippet="cache hit", context_sources=["retrieval_cache"])
    r = build_fused_prompt("text_replacement", target_file="f.py", file_content="x=1",
                           hybrid_context=ctx)
    assert "cache hit" in r.prompt or r.context_sources


def test_context_sources_from_hybrid():
    ctx = _ctx(search_snippet="found stuff", context_sources=["search"])
    r = build_fused_prompt("text_replacement", target_file="f.py", file_content="x=1",
                           hybrid_context=ctx)
    assert "search" in r.context_sources


def test_no_hybrid_context_works():
    r = build_fused_prompt("text_replacement", target_file="f.py", file_content="x=1",
                           hybrid_context=None)
    assert isinstance(r.prompt, str)


# --- target_file preserved ---

def test_target_file_preserved():
    r = build_fused_prompt("text_replacement", target_file="my/file.py", file_content="")
    assert r.target_file == "my/file.py"


# --- package surface ---

def test_package_surface():
    import framework
    assert hasattr(framework, "FusedPromptContext")
    assert hasattr(framework, "build_fused_prompt")
